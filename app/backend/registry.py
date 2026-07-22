"""Harness registry — what's promoted, what's quarantined.

Stores workflow specs and generated-tool specs. Truth lives in the
``Store`` (filesystem in v0.1, MinIO later); the registry maintains an
in-memory index and rebuilds it from the store on startup.

The dispatcher uses ``lookup(intent_text)`` to find a promoted hit for an
incoming request.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Optional

from .store import Store
from .trace import intent_hash, normalize_intent
from .workflow import WorkflowSpec, WorkflowStatus


@dataclass
class GeneratedToolSpec:
    """A code-genned tool produced from a hot workflow (Layer C)."""

    tool_id: str
    workflow_id: str
    version: int
    disk_path: str       # Where the .py lives in the project tree
    store_key: str       # Where the .py also lives in the store (truth)
    tests_passed: bool


@dataclass
class PromotedHit:
    """A registry lookup hit — either a workflow or a generated tool."""

    kind: str  # "workflow" | "generated_tool"
    id: str
    workflow: WorkflowSpec
    generated_tool: GeneratedToolSpec | None = None

    @property
    def harness_hit_label(self) -> str:
        if self.kind == "generated_tool" and self.generated_tool is not None:
            return f"generated:{self.generated_tool.tool_id}"
        return f"workflow:{self.id}"


class HarnessRegistry:
    """In-memory index over store-backed workflows + generated tools.

    Lookup uses normalized intent fingerprint. A workflow is considered a
    candidate when:
      - its status is ACTIVE or COMPILED, and
      - the incoming intent_hash matches the workflow's recorded
        intent_hash (stored when the workflow was promoted).
    """

    WORKFLOW_PREFIX = "workflows"
    GENERATED_PREFIX = "generated"

    def __init__(self, store: Store) -> None:
        self._store = store
        self._workflows: dict[str, WorkflowSpec] = {}
        self._intent_to_workflow: dict[str, str] = {}
        self._generated: dict[str, GeneratedToolSpec] = {}
        self._workflow_intent_hashes: dict[str, str] = {}

    def reset(self) -> None:
        """Drop the in-memory index and reload from the (current) store.

        Use after wiping learned state from the store so the registry doesn't
        keep serving workflows that were loaded at startup. Without this, a
        bundle built before the store was cleared would still warm-hit.
        """
        self._workflows.clear()
        self._intent_to_workflow.clear()
        self._generated.clear()
        self._workflow_intent_hashes.clear()
        self.load()

    def load(self) -> None:
        """Rebuild the in-memory index from the store."""
        for key in self._store.list(self.WORKFLOW_PREFIX):
            if not key.endswith(".yaml"):
                continue
            spec = WorkflowSpec.from_yaml(self._store.get(key))
            self._workflows[spec.id] = spec
            # Intent hash recovered from the first keyword cluster. We also
            # store it on save so we don't have to re-derive on every load.
            ih = _intent_hash_from_keywords(spec.intent_keywords)
            self._intent_to_workflow[ih] = spec.id
            self._workflow_intent_hashes[spec.id] = ih

    # ----- workflows -----

    def register_workflow(self, spec: WorkflowSpec) -> str:
        """Insert/upsert a workflow into the registry + store."""
        key = self._workflow_key(spec.id)
        self._store.put(key, spec.to_yaml())
        self._workflows[spec.id] = spec
        ih = _intent_hash_from_keywords(spec.intent_keywords)
        self._intent_to_workflow[ih] = spec.id
        self._workflow_intent_hashes[spec.id] = ih
        return key

    def list_workflows(
        self, status: WorkflowStatus | None = None
    ) -> list[WorkflowSpec]:
        items = list(self._workflows.values())
        if status is not None:
            items = [w for w in items if w.status == status]
        return items

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowSpec]:
        return self._workflows.get(workflow_id)

    def activate(self, workflow_id: str) -> None:
        wf = self._workflows[workflow_id]
        wf.status = WorkflowStatus.ACTIVE
        self.register_workflow(wf)

    def quarantine(self, workflow_id: str, reason: str = "") -> None:
        wf = self._workflows.get(workflow_id)
        if wf is None:
            return
        wf.status = WorkflowStatus.QUARANTINED
        self.register_workflow(wf)
        self._store.put(
            f"needs_review/workflow/{workflow_id}.json",
            f'{{"reason": {reason!r}, "workflow_id": "{workflow_id}"}}',
        )

    def bump_hits(self, workflow_id: str) -> int:
        wf = self._workflows[workflow_id]
        wf.hits += 1
        self.register_workflow(wf)
        return wf.hits

    # ----- generated tools -----

    def register_generated_tool(self, spec: GeneratedToolSpec) -> None:
        self._generated[spec.tool_id] = spec
        wf = self._workflows.get(spec.workflow_id)
        if wf is not None and spec.tests_passed:
            wf.status = WorkflowStatus.COMPILED
            self.register_workflow(wf)

    def get_generated_tool(self, tool_id: str) -> Optional[GeneratedToolSpec]:
        return self._generated.get(tool_id)

    # ----- lookup -----

    def lookup(self, intent_text: str) -> PromotedHit | None:
        ih = intent_hash(intent_text)
        wf_id = self._intent_to_workflow.get(ih)
        if wf_id is None:
            return None
        wf = self._workflows[wf_id]
        if wf.status == WorkflowStatus.QUARANTINED:
            return None
        if wf.status == WorkflowStatus.DRAFT:
            return None
        # Prefer a generated tool if one exists.
        gen = next(
            (g for g in self._generated.values() if g.workflow_id == wf_id),
            None,
        )
        if gen is not None and gen.tests_passed:
            return PromotedHit(
                kind="generated_tool",
                id=gen.tool_id,
                workflow=wf,
                generated_tool=gen,
            )
        return PromotedHit(kind="workflow", id=wf.id, workflow=wf)

    # ----- helpers -----

    @staticmethod
    def _workflow_key(workflow_id: str) -> str:
        return str(PurePosixPath("workflows") / f"{workflow_id}.yaml")


def _intent_hash_from_keywords(keywords: list[str]) -> str:
    """Reproduce the intent hash of the original cluster from the keywords.

    The compiler stripped param-like tokens, so re-normalizing the joined
    keywords yields the same hash as the original normalize_intent on the
    cluster's sample. Good enough for v0.1.
    """
    return intent_hash(normalize_intent(" ".join(keywords)))
