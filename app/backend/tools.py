"""Tool registry — what an agent can call.

A ``Tool`` is just an async callable with a name and a JSON-shaped signature.
v0.1 includes stub scraper tools (fetch_url, parse_listing) that return
canned data — enough to demonstrate the learning loop without pulling in
the real crawl4ai dependency chain. Real tools will replace these by
satisfying the same ``Tool`` protocol.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


# A tool is an async function taking kwargs and returning anything JSON-able.
ToolFn = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    fn: ToolFn
    description: str = ""
    # Approximate token cost when invoked via LLM-driven path. 0 for cheap
    # mechanical tools; non-zero for vision/LLM-backed ones.
    llm_cost_tokens: int = 0


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._tools


# ---------- stub scraper tools (replace with real crawl4ai in v1) ----------


@dataclass
class _FakeWeb:
    """Deterministic fake HTML keyed by URL. Used by the demo + tests."""

    pages: dict[str, str] = field(default_factory=dict)

    def html_for(self, url: str) -> str:
        if url in self.pages:
            return self.pages[url]
        # Synthesize a listing-like HTML page that varies by URL.
        seed = hashlib.md5(url.encode()).hexdigest()[:8]
        return (
            "<html><body>"
            f"<h1>Listing {seed}</h1>"
            f'<div class="price">${int(seed, 16) % 9000 + 1000}</div>'
            f'<div class="bedrooms">{int(seed[0], 16) % 5 + 1}</div>'
            f'<div class="address">{seed} Main St</div>'
            "</body></html>"
        )


def build_default_tool_registry(
    web: _FakeWeb | None = None, llm_tokens_per_reason: int = 350
) -> tuple[ToolRegistry, _FakeWeb]:
    """Returns (registry, web). web is exposed so the demo can preload pages."""
    web = web or _FakeWeb()

    async def fetch_url(url: str) -> str:
        # Simulate a small network roundtrip so warm-vs-cold timing is visible.
        await asyncio.sleep(0.02)
        return web.html_for(url)

    async def parse_listing(html: str) -> dict[str, Any]:
        await asyncio.sleep(0.005)
        # Toy parser: extract by exact tag pattern. Good enough for the demo.
        def _extract(tag: str, html: str) -> str:
            marker = f'class="{tag}">'
            i = html.find(marker)
            if i < 0:
                return ""
            j = html.find("<", i + len(marker))
            return html[i + len(marker) : j]
        return {
            "price": _extract("price", html),
            "bedrooms": _extract("bedrooms", html),
            "address": _extract("address", html),
        }

    async def format_listing(listing: dict[str, Any]) -> str:
        await asyncio.sleep(0.002)
        return (
            f"Price: {listing.get('price', '?')}\n"
            f"Bedrooms: {listing.get('bedrooms', '?')}\n"
            f"Address: {listing.get('address', '?')}"
        )

    reg = ToolRegistry()
    reg.register(
        Tool(
            name="fetch_url",
            fn=fetch_url,
            description="Fetch a URL and return its raw HTML",
            llm_cost_tokens=0,
        )
    )
    reg.register(
        Tool(
            name="parse_listing",
            fn=parse_listing,
            description="Extract listing fields from HTML",
            llm_cost_tokens=0,
        )
    )
    reg.register(
        Tool(
            name="format_listing",
            fn=format_listing,
            description="Format extracted listing for human display",
            llm_cost_tokens=0,
        )
    )
    return reg, web
