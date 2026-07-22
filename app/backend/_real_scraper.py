"""Real scraper tools: plain-HTTP fetch + BeautifulSoup + LLM extraction.

Fetch is a normal HTTP GET (httpx) with a full browser-like header set — no
headless browser, since automation fingerprints get blocked. The fetched HTML
is reduced to visible text (BeautifulSoup), then the configured LLM extracts
the listing fields. The factory wires these in when BeautifulSoup is importable;
otherwise the stub tools from ``tools.py`` keep the demo runnable.
"""

from __future__ import annotations

from typing import Any

from .tools import Tool, ToolRegistry


try:  # pragma: no cover - environment-dependent
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig  # type: ignore

    CRAWL4AI_AVAILABLE = True
except Exception:  # noqa: BLE001
    AsyncWebCrawler = None  # type: ignore[assignment]
    BrowserConfig = None  # type: ignore[assignment]
    CrawlerRunConfig = None  # type: ignore[assignment]
    CRAWL4AI_AVAILABLE = False

try:  # pragma: no cover
    from bs4 import BeautifulSoup  # type: ignore

    BS4_AVAILABLE = True
except Exception:  # noqa: BLE001
    BeautifulSoup = None  # type: ignore[assignment]
    BS4_AVAILABLE = False


def is_configured() -> bool:
    # HTTP fetch (httpx) + HTML→text (bs4). No headless browser required.
    return BS4_AVAILABLE


_MAX_CONTENT_CHARS = 12000

# Browser-like headers so plain HTTP requests look like a real browser. We do
# NOT drive a headless browser (those get fingerprinted + blocked) — just a
# normal HTTP GET with a full header set, which many sites serve fine.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
}


def _html_to_text(html: str) -> str:
    """Strip an HTML document down to visible, listing-relevant text."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "template",
                     "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # Collapse whitespace runs so the LLM sees dense content, not blank lines.
    return " ".join(text.split())


async def _real_fetch_url(url: str) -> str:
    """Fetch a URL over plain HTTP (no browser) and return visible text.

    Uses httpx with a full browser-like header set. Returns a ``FETCH_FAILED``
    sentinel on network errors or bot-walls (non-2xx) so the parser surfaces
    the failure honestly instead of hallucinating fields.
    """
    import httpx

    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, follow_redirects=True, timeout=30.0
        ) as client:
            resp = await client.get(url)
    except Exception as exc:  # noqa: BLE001
        return f"FETCH_FAILED: {type(exc).__name__}: {exc}"
    if resp.status_code >= 400:
        return f"FETCH_FAILED: HTTP {resp.status_code} for {url}"
    text = _html_to_text(resp.text)
    if not text:
        return f"FETCH_FAILED: empty body (HTTP {resp.status_code})"
    return text[:_MAX_CONTENT_CHARS]


_EXTRACT_SYSTEM = """\
You extract structured fields from the text of a real-estate listing page.
Return STRICT JSON only — no prose, no markdown fences. Schema:
  {"price": <string or null>,
   "bedrooms": <string or null>,
   "address": <string or null>}
Use null for any field that is not clearly present in the text. Copy values
verbatim from the page (e.g. price as shown like "$1,250,000"). Do not guess.
"""


async def _extract_with_llm(content: str) -> str:
    """Ask the local model for the listing fields as JSON text.

    qwen3-class models are reasoning models: on Ollama's OpenAI-compat (/v1)
    endpoint their hidden thinking silently consumes the whole token budget
    and ``content`` comes back empty. Ollama's *native* /api/chat endpoint
    supports ``think:false``, which yields the answer directly — so when the
    base URL is Ollama we call that. Anything else uses the OpenAI-compat path.
    """
    from . import _llm

    base = (_llm.configured_base_url() or "").rstrip("/")
    model = _llm.configured_model()
    messages = [
        {"role": "system", "content": _EXTRACT_SYSTEM},
        {"role": "user", "content": content},
    ]

    if base.endswith("/v1") and ("11434" in base or "ollama" in base.lower()):
        import httpx

        native = base[: -len("/v1")] + "/api/chat"
        payload = {
            "model": model,
            "think": False,
            "stream": False,
            "options": {"temperature": 0, "num_predict": 400},
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=60.0) as hc:
            r = await hc.post(native, json=payload)
            r.raise_for_status()
            return (r.json().get("message", {}) or {}).get("content", "") or ""

    # Generic OpenAI-compatible backend.
    client = _llm._build_client()
    resp = await client.chat.completions.create(
        model=model, messages=messages, temperature=0.0, max_tokens=400
    )
    return (resp.choices[0].message.content or "").strip()


async def _real_parse_listing(html: str) -> dict[str, Any]:
    """Extract listing fields from page content using the configured LLM.

    The parameter is named ``html`` to match the stub tool's contract (and the
    workflows/generated tools learned against it), though with the real fetcher
    it actually receives cleaned markdown.
    """
    from . import _llm

    content = html
    if content.startswith("FETCH_FAILED"):
        return {"price": None, "bedrooms": None, "address": None,
                "error": content}
    if not _llm.is_configured():
        # No LLM to extract with — fall back to the naive class scrape so the
        # tool still returns something deterministic.
        soup = BeautifulSoup(content, "lxml")
        def _by_class(name: str) -> str:
            node = soup.find(attrs={"class": name})
            return node.get_text(strip=True) if node else ""
        return {"price": _by_class("price"), "bedrooms": _by_class("bedrooms"),
                "address": _by_class("address")}

    import json
    import re

    text = (await _extract_with_llm(content)).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"price": None, "bedrooms": None, "address": None}
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return {"price": None, "bedrooms": None, "address": None}
    return {
        "price": obj.get("price"),
        "bedrooms": obj.get("bedrooms"),
        "address": obj.get("address"),
    }


async def _real_format_listing(listing: Any) -> str:
    # Idempotent: a learned workflow may chain format_listing onto its own
    # output (already a string) — return it unchanged rather than crashing.
    if isinstance(listing, str):
        return listing
    if not isinstance(listing, dict):
        return str(listing)
    if listing.get("error"):
        return f"Could not scrape listing: {listing['error']}"

    def _show(v: Any) -> str:
        return str(v) if v not in (None, "", "null") else "(not found)"

    return (
        f"Price: {_show(listing.get('price'))}\n"
        f"Bedrooms: {_show(listing.get('bedrooms'))}\n"
        f"Address: {_show(listing.get('address'))}"
    )


def install_real_scraper_tools(registry: ToolRegistry) -> bool:
    """Replace the stub scraper tools with real crawl4ai-backed ones.

    Returns True when the swap happened, False when deps were missing
    and the stub tools were left in place.
    """
    if not is_configured():
        return False
    registry.register(
        Tool(
            name="fetch_url",
            fn=_real_fetch_url,
            description="Fetch a URL over HTTP and return the page's visible text",
            llm_cost_tokens=0,
        )
    )
    registry.register(
        Tool(
            name="parse_listing",
            fn=_real_parse_listing,
            description="Extract listing fields (price, bedrooms, address) from page text using the LLM",
            llm_cost_tokens=0,
        )
    )
    registry.register(
        Tool(
            name="format_listing",
            fn=_real_format_listing,
            description="Render a listing dict for human display",
            llm_cost_tokens=0,
        )
    )
    return True


async def shutdown_real_scraper() -> None:
    # HTTP fetch uses a per-request client; nothing persistent to close.
    return None
