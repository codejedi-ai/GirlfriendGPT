"""Auto-generated tool from workflow scrape_listing.

Compiled-from-YAML version. Do not edit; re-run codegen to update.
"""

from __future__ import annotations

from typing import Any


WORKFLOW_ID = 'scrape_listing'
VERSION = 1


async def run(tools, params: dict[str, Any]) -> Any:
    # Validate required params (mirrors WorkflowRunner).
    missing = [p for p in ['url'] if p not in params]
    if missing:
        raise ValueError(
            f'generated tool {WORKFLOW_ID!r} missing params: {missing}'
        )
    ctx: dict[str, Any] = {'params': params}
    args = _resolve_args({"url": "{{ params.url }}"}, ctx)
    result = await tools.get('fetch_url').fn(**args)
    ctx['fetch_url_0'] = result
    args = _resolve_args({"html": "{{ fetch_url_0 }}"}, ctx)
    result = await tools.get('parse_listing').fn(**args)
    ctx['parse_listing_1'] = result
    args = _resolve_args({"listing": "{{ parse_listing_1 }}"}, ctx)
    result = await tools.get('format_listing').fn(**args)
    ctx['format_listing_2'] = result

    return _resolve_template('{{ format_listing_2 }}', ctx)


# --- inlined template renderer (kept identical to runner.render) ---

import re as _re

_T = _re.compile(r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*\}\}')

def _resolve_path(path, ctx):
    cur = ctx
    for p in path.split('.'):
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            cur = getattr(cur, p, None)
        if cur is None:
            return None
    return cur

def _resolve_template(tpl, ctx):
    if not isinstance(tpl, str):
        return tpl
    m = _T.fullmatch(tpl.strip())
    if m is not None:
        return _resolve_path(m.group(1), ctx)
    return _T.sub(lambda mm: str(_resolve_path(mm.group(1), ctx)), tpl)

def _resolve_args(args, ctx):
    out = {}
    for k, v in args.items():
        if isinstance(v, str):
            out[k] = _resolve_template(v, ctx)
        elif isinstance(v, dict):
            out[k] = _resolve_args(v, ctx)
        elif isinstance(v, list):
            out[k] = [_resolve_template(x, ctx) if isinstance(x, str) else x for x in v]
        else:
            out[k] = v
    return out
