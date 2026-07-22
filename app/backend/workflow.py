"""WorkflowSpec — the YAML artifact promoted from trace clusters.

A workflow is a named sequence of tool calls with Jinja-rendered args.
The dispatcher invokes a workflow as one step (skipping LLM reasoning),
the ``WorkflowRunner`` executes it against the tool registry.

See design §8.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml


class WorkflowStatus(str, Enum):
    DRAFT = "draft"          # Just compiled, awaiting first run
    ACTIVE = "active"        # Replaying successfully
    QUARANTINED = "quarantined"  # Last run regressed; do not use
    COMPILED = "compiled"    # Has a code-genned tool (Layer C done)


@dataclass
class WorkflowStep:
    tool: str
    args: dict[str, Any]
    bind: str | None = None  # Name under which to store the result in ctx


@dataclass
class WorkflowSpec:
    """One promoted workflow. Source of truth lives in the store."""

    id: str
    version: int
    intent_keywords: list[str]
    required_params: list[str]
    steps: list[WorkflowStep]
    output_template: str
    source_traces: list[str] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.DRAFT
    hits: int = 0

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            {
                "workflow": {
                    "id": self.id,
                    "version": self.version,
                    "trigger": {
                        "intent_keywords": self.intent_keywords,
                        "required_params": self.required_params,
                    },
                    "steps": [
                        {
                            "tool": s.tool,
                            "args": s.args,
                            **({"bind": s.bind} if s.bind else {}),
                        }
                        for s in self.steps
                    ],
                    "output": self.output_template,
                    "source_traces": list(self.source_traces),
                    "status": self.status.value,
                    "hits": self.hits,
                }
            },
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, blob: bytes | str) -> "WorkflowSpec":
        if isinstance(blob, bytes):
            blob = blob.decode("utf-8")
        root = yaml.safe_load(blob)
        wf = root["workflow"]
        trig = wf.get("trigger", {})
        return cls(
            id=wf["id"],
            version=int(wf["version"]),
            intent_keywords=list(trig.get("intent_keywords", [])),
            required_params=list(trig.get("required_params", [])),
            steps=[
                WorkflowStep(
                    tool=s["tool"],
                    args=dict(s.get("args", {})),
                    bind=s.get("bind"),
                )
                for s in wf["steps"]
            ],
            output_template=wf.get("output", ""),
            source_traces=list(wf.get("source_traces", [])),
            status=WorkflowStatus(wf.get("status", "draft")),
            hits=int(wf.get("hits", 0)),
        )
