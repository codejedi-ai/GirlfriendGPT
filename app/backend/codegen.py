"""Deterministic codegen — turn a WorkflowSpec into a real Python function.

This is the v0.1 stand-in for the LLM tool codegen described in design
§8.3. The output is honest: a hand-templated module that calls the same
tools the workflow does, in the same order, with the same arg shape.

When ``HARNESS_USE_LLM_CODEGEN=1`` and the LLM client is wired, the same
contract (input: WorkflowSpec; output: Python source string + module
path) gets satisfied by a real LLM call. The deterministic templater
remains as the fallback / regression baseline.

Generated tools live in two places (truth in store, runtime on disk):
- Store key: ``generated/{tool_id}.py``
- Disk path: ``app/agents/harness/generated/{tool_id}.py``

The disk copy makes "the agent appears to edit itself" real — it's confined
to one package, registered through ``HarnessRegistry``, and gated by the
regression-test step before activation.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from .registry import GeneratedToolSpec, HarnessRegistry
from .store import Store
from .workflow import WorkflowSpec


GENERATED_PKG_DIR = (
    Path(__file__).parent / "generated"
)


def _ensure_generated_pkg() -> None:
    GENERATED_PKG_DIR.mkdir(exist_ok=True)
    init = GENERATED_PKG_DIR / "__init__.py"
    if not init.exists():
        init.write_text(
            '"""Auto-generated tool package — do not edit by hand.\n\n'
            "Modules here are produced by ``codegen.codegen_from_workflow``\n"
            "from a promoted workflow's source traces. The harness registry\n"
            "is the source of truth for which modules are active.\n"
            '"""\n',
            encoding="utf-8",
        )


def codegen_source(spec: WorkflowSpec) -> str:
    """Emit a Python module string that runs the workflow programmatically.

    The generated function ``run`` takes a tool registry + params dict and
    returns the same output the workflow would. It's the same code path
    as ``WorkflowRunner``, just inlined — so a successful codegen exists
    to *skip the YAML interpreter step* and call the tools directly.
    """
    header = [
        '"""Auto-generated tool from workflow ' + spec.id + ".",
        "",
        "Compiled-from-YAML version. Do not edit; re-run codegen to update.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        "",
        "WORKFLOW_ID = " + repr(spec.id),
        "VERSION = " + repr(spec.version),
        "",
        "",
        "async def run(tools, params: dict[str, Any]) -> Any:",
        "    # Validate required params (mirrors WorkflowRunner).",
        "    missing = [p for p in " + repr(spec.required_params) + " if p not in params]",
        "    if missing:",
        "        raise ValueError(",
        "            f'generated tool {WORKFLOW_ID!r} missing params: {missing}'",
        "        )",
        "    ctx: dict[str, Any] = {'params': params}",
    ]
    body: list[str] = []
    for step in spec.steps:
        # Build a dict-literal of args with template strings preserved; we
        # resolve them at run time via a tiny inlined render function so the
        # generated module stays self-contained.
        body.append(
            f"    args = _resolve_args({json.dumps(step.args)}, ctx)"
        )
        body.append(f"    result = await tools.get({step.tool!r}).fn(**args)")
        if step.bind:
            body.append(f"    ctx[{step.bind!r}] = result")
    body.append("")
    if spec.output_template:
        body.append(
            f"    return _resolve_template({spec.output_template!r}, ctx)"
        )
    else:
        body.append("    return result")

    footer = [
        "",
        "",
        "# --- inlined template renderer (kept identical to runner.render) ---",
        "",
        "import re as _re",
        "",
        "_T = _re.compile(r'\\{\\{\\s*([a-zA-Z_][a-zA-Z0-9_.]*)\\s*\\}\\}')",
        "",
        "def _resolve_path(path, ctx):",
        "    cur = ctx",
        "    for p in path.split('.'):",
        "        if isinstance(cur, dict):",
        "            cur = cur.get(p)",
        "        else:",
        "            cur = getattr(cur, p, None)",
        "        if cur is None:",
        "            return None",
        "    return cur",
        "",
        "def _resolve_template(tpl, ctx):",
        "    if not isinstance(tpl, str):",
        "        return tpl",
        "    m = _T.fullmatch(tpl.strip())",
        "    if m is not None:",
        "        return _resolve_path(m.group(1), ctx)",
        "    return _T.sub(lambda mm: str(_resolve_path(mm.group(1), ctx)), tpl)",
        "",
        "def _resolve_args(args, ctx):",
        "    out = {}",
        "    for k, v in args.items():",
        "        if isinstance(v, str):",
        "            out[k] = _resolve_template(v, ctx)",
        "        elif isinstance(v, dict):",
        "            out[k] = _resolve_args(v, ctx)",
        "        elif isinstance(v, list):",
        "            out[k] = [_resolve_template(x, ctx) if isinstance(x, str) else x for x in v]",
        "        else:",
        "            out[k] = v",
        "    return out",
        "",
    ]
    return "\n".join(header + body + footer)


def codegen_from_workflow(
    spec: WorkflowSpec, store: Store, registry: HarnessRegistry
) -> GeneratedToolSpec:
    """Generate, write to store + disk, regress-test, register."""
    _ensure_generated_pkg()
    src = codegen_source(spec)
    tool_id = f"{spec.id}_v{spec.version}"
    store_key = f"generated/{tool_id}.py"
    disk_path = GENERATED_PKG_DIR / f"{tool_id}.py"

    store.put(store_key, src)
    disk_path.write_text(src, encoding="utf-8")

    gen_spec = GeneratedToolSpec(
        tool_id=tool_id,
        workflow_id=spec.id,
        version=spec.version,
        disk_path=str(disk_path),
        store_key=store_key,
        tests_passed=False,
    )
    registry.register_generated_tool(gen_spec)
    return gen_spec


def import_generated(tool_id: str):
    """Import a generated module from disk, bypassing module cache."""
    mod_name = f"harness.generated.{tool_id}"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    disk_path = GENERATED_PKG_DIR / f"{tool_id}.py"
    spec = importlib.util.spec_from_file_location(mod_name, disk_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generated module at {disk_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


async def regression_test_generated(
    gen: GeneratedToolSpec,
    workflow: WorkflowSpec,
    tools,
    sample_params: dict,
    expected_output_check,
) -> bool:
    """Run the generated module against a sample input.

    ``expected_output_check`` is a callable taking the output and returning
    True/False. The caller (reflection worker) typically derives a check
    from one of the source traces' results.
    """
    mod = import_generated(gen.tool_id)
    try:
        output = await mod.run(tools, sample_params)
    except Exception:
        return False
    return bool(expected_output_check(output))
