"""Real LLM policy + codegen via OpenAI-compatible API.

Targets the user's HF stack:
    OPENAI_API_BASE   — base URL (e.g. https://router.huggingface.co/v1)
    HF_TOKEN          — bearer token
    CONFIGCLAW_AGENT_MODEL — model id (defaults to a small instruct model)

Same call sites as the v0.1 deterministic policy/codegen. The factory
swaps these in when the ``openai`` SDK is importable AND the env is set.
Otherwise the dispatcher keeps the mock policy / templated codegen and
the demo still runs end-to-end.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any


try:  # pragma: no cover - environment-dependent
    from openai import AsyncOpenAI  # type: ignore

    REAL_AVAILABLE = True
except Exception:  # noqa: BLE001
    AsyncOpenAI = None  # type: ignore[assignment]
    REAL_AVAILABLE = False


_DEFAULT_LOCAL_BASE = "http://localhost:11434/v1"  # Ollama default.
_DEFAULT_LOCAL_MODEL = "qwen3.5:latest"
_DEFAULT_LOCAL_API_KEY = "local"  # Ollama ignores this but openai SDK needs a value.


def _resolved_config() -> tuple[str, str, str] | None:
    """Return (base_url, api_key, model) or None when nothing is configured.

    Precedence (first match wins):
      1. HARNESS_LLM_BASE_URL + HARNESS_LLM_MODEL  — explicit local mode
         (Ollama / llama.cpp / vLLM / LM Studio). HARNESS_LLM_API_KEY
         defaults to "local" when not set.
      2. OPENAI_API_BASE + HF_TOKEN + CONFIGCLAW_AGENT_MODEL — the
         existing HF-router setup. Kept for back-compat.
      3. Localhost Ollama default (http://localhost:11434/v1, llama3.1:8b)
         when no env is set — relies on caller's reachability check.
    """
    base = os.environ.get("HARNESS_LLM_BASE_URL")
    model = os.environ.get("HARNESS_LLM_MODEL")
    if base and model:
        return (
            base,
            os.environ.get("HARNESS_LLM_API_KEY", _DEFAULT_LOCAL_API_KEY),
            model,
        )
    if os.environ.get("OPENAI_API_BASE") and os.environ.get("HF_TOKEN"):
        return (
            os.environ["OPENAI_API_BASE"],
            os.environ["HF_TOKEN"],
            os.environ.get(
                "CONFIGCLAW_AGENT_MODEL",
                "meta-llama/Meta-Llama-3.1-8B-Instruct",
            ),
        )
    # Last-ditch: assume default local Ollama. is_reachable() decides.
    return (_DEFAULT_LOCAL_BASE, _DEFAULT_LOCAL_API_KEY, _DEFAULT_LOCAL_MODEL)


def is_configured() -> bool:
    """True when an LLM client can be constructed (SDK + some config)."""
    if not REAL_AVAILABLE:
        return False
    return _resolved_config() is not None


async def is_reachable(timeout_s: float = 2.0) -> bool:
    """True when the configured endpoint actually responds.

    Sends a HEAD/GET to the base URL's ``/models`` (OpenAI-compat convention).
    Used by the factory to distinguish "configured but service is down" from
    "configured and live"; both Ollama and llama.cpp / vLLM serve /models.
    """
    if not REAL_AVAILABLE:
        return False
    cfg = _resolved_config()
    if cfg is None:
        return False
    base, _api_key, _model = cfg
    try:
        import urllib.request as ur
        url = base.rstrip("/") + "/models"
        req = ur.Request(url, method="GET")
        await _to_thread_call(_open_short, req, timeout_s)
        return True
    except Exception:
        return False


import asyncio  # noqa: E402  (kept low for clarity; used by reachability check)


async def _to_thread_call(fn, *args):
    return await asyncio.to_thread(fn, *args)


def _open_short(req, timeout_s: float) -> int:
    import urllib.request as ur
    with ur.urlopen(req, timeout=timeout_s) as resp:
        return resp.status


def _build_client() -> Any:
    if not REAL_AVAILABLE:
        raise RuntimeError("openai SDK not installed")
    cfg = _resolved_config()
    if cfg is None:
        raise RuntimeError(
            "no LLM configured; set HARNESS_LLM_BASE_URL+HARNESS_LLM_MODEL "
            "for local Ollama/llama.cpp/vLLM, or OPENAI_API_BASE+HF_TOKEN "
            "for HF router"
        )
    base_url, api_key, _model = cfg
    return AsyncOpenAI(base_url=base_url, api_key=api_key)


def configured_model() -> str | None:
    cfg = _resolved_config()
    return cfg[2] if cfg is not None else None


def configured_base_url() -> str | None:
    cfg = _resolved_config()
    return cfg[0] if cfg is not None else None


# ---------- Real LLM policy ----------


_POLICY_SYSTEM = """\
You are a tool-using agent that completes a user's goal by calling tools ONE
AT A TIME.

You will be shown the user's goal, the available tools (name: description),
and the results you have already obtained ("context"), each stored under a
name.

Choose the SINGLE next tool call that makes progress. Reply with STRICT JSON
ONLY — no prose, no markdown fences. Schema:
  {"tool": "<tool name or 'done'>",
   "args": {"<arg_name>": "<value-or-{{bind}}>"},
   "bind": "<short snake_case name to store the result under>"}

Rules:
  - To pass a previous result as an argument, use the token {{name}} where
    name is the bind of that earlier result. Never paste raw content.
  - To pass a request parameter, use {{params.<name>}} (e.g. {{params.url}}).
  - Always give a short snake_case "bind" name when calling a tool.
  - Never call the same tool twice with the same args; advance the pipeline.
  - Raw fetched HTML is NOT a human answer. After fetch_url you MUST parse it,
    then format it, before finishing.
  - Reply {"tool": "done"} ONLY when a human-readable final answer already
    exists in context (e.g. a formatted result), or when no tool can help.

Worked example for scraping a listing URL:
  step 1 -> {"tool":"fetch_url","args":{"url":"{{params.url}}"},"bind":"html"}
  step 2 -> {"tool":"parse_listing","args":{"html":"{{html}}"},"bind":"listing"}
  step 3 -> {"tool":"format_listing","args":{"listing":"{{listing}}"},"bind":"formatted"}
  step 4 -> {"tool":"done"}
"""


def _summarize_ctx_value(value: Any) -> str:
    """Opaque, progress-oriented summary of a bound result.

    The small local model tends to stop early if it sees the raw HTML (it
    thinks the answer is "right there") — so we describe WHAT was obtained and
    that it still needs processing, rather than dumping the bytes.
    """
    if isinstance(value, str) and ("<html" in value.lower() or "</" in value):
        return f"<raw HTML document, {len(value)} chars — not yet parsed>"
    if isinstance(value, dict):
        return (
            f"<parsed data dict with keys {list(value.keys())} "
            "— not yet formatted for display>"
        )
    s = str(value)
    return s if len(s) <= 200 else s[:200] + "..."


class OpenAILLMPolicy:
    """LLM-driven action selection. One call per dispatcher loop step."""

    # Approximate cost — used by the dispatcher for the cold-vs-warm
    # delta. Updated from the API response when available.
    cost_per_call = 350

    def __init__(self, model: str | None = None) -> None:
        if not REAL_AVAILABLE:
            raise RuntimeError("openai SDK not installed; use mock policy")
        self._client = _build_client()
        self._model = model or configured_model() or _DEFAULT_LOCAL_MODEL

    async def choose(
        self, intent: str, ctx: dict[str, Any]
    ) -> tuple[str, dict, str]:
        tool_catalogue = ctx.get("_tools_catalogue", "")
        bound = [
            (k, v)
            for k, v in ctx.items()
            if not k.startswith("_") and k != "params"
        ]
        if bound:
            ctx_lines = "\n".join(
                f"  {k} = {_summarize_ctx_value(v)}" for k, v in bound
            )
        else:
            ctx_lines = "  (empty)"
        prompt = (
            f"User goal: {intent}\n"
            f"Params: {ctx.get('params', {})}\n"
            f"Available tools:\n{tool_catalogue}\n"
            f"Context (results so far):\n{ctx_lines}\n"
        )
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _POLICY_SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        # Track actual usage when the provider reports it.
        try:
            self.cost_per_call = int(resp.usage.completion_tokens or 0) + int(
                resp.usage.prompt_tokens or 0
            )
        except Exception:
            pass
        text = (resp.choices[0].message.content or "").strip()
        return _parse_choice(text)


def _parse_choice(text: str) -> tuple[str, dict, str]:
    """Best-effort JSON extraction — LLMs love to wrap output in backticks."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return "done", {}, ""
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return "done", {}, ""
    tool = str(obj.get("tool", "done"))
    args = obj.get("args", {}) or {}
    bind = str(obj.get("bind", "")) if obj.get("bind") else ""
    if not isinstance(args, dict):
        args = {}
    return tool, args, bind


# ---------- Real LLM codegen ----------


_CODEGEN_SYSTEM = """\
You are emitting a single Python module that implements a tool function.
The function signature MUST be:

    async def run(tools, params: dict) -> Any: ...

Constraints:
- Only `await tools.get('<name>').fn(**args)` is allowed for tool calls.
- Use the exact tool names and step order described.
- Substitute params and prior-step results as instructed.
- Return the workflow's output template at the end.
- DO NOT import anything beyond `from __future__ import annotations` and
  `from typing import Any`. Helpers must be inlined.

Reply with the module source ONLY — no markdown fences, no commentary.
"""


class OpenAILLMCodegen:
    """LLM-driven WorkflowSpec -> Python module compilation."""

    def __init__(self, model: str | None = None) -> None:
        if not REAL_AVAILABLE:
            raise RuntimeError("openai SDK not installed; use deterministic codegen")
        self._client = _build_client()
        self._model = model or configured_model() or _DEFAULT_LOCAL_MODEL

    async def emit_source(self, workflow_yaml: str) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _CODEGEN_SYSTEM},
                {"role": "user", "content": workflow_yaml},
            ],
            temperature=0.0,
            max_tokens=1200,
        )
        src = (resp.choices[0].message.content or "").strip()
        # Strip markdown fences if the model added them despite the prompt.
        if src.startswith("```"):
            src = src.split("\n", 1)[1] if "\n" in src else ""
            if src.endswith("```"):
                src = src.rsplit("```", 1)[0]
        return src.rstrip() + "\n"
