# Slim image for the self-improving harness AI (HTTP scraper + LLM).
# Deliberately minimal: the harness uses plain-HTTP fetch + BeautifulSoup, so
# none of the crawl4ai/playwright/torch chain is needed.
FROM python:3.12-slim

# uv for dependency install (project convention: "Any Python please use uv").
RUN pip install --no-cache-dir uv

# Exact runtime deps for app/agents/harness + the gateway router + the launcher.
RUN uv pip install --system --no-cache \
    "fastapi>=0.110" \
    "uvicorn[standard]>=0.29" \
    "structlog>=24.1" \
    "pyyaml>=6.0" \
    "openai>=1.0" \
    "redis>=5.0" \
    "minio>=7.2" \
    "asyncpg>=0.29" \
    "beautifulsoup4>=4.12" \
    "lxml>=5.0" \
    "httpx>=0.27"

WORKDIR /workspace

# Source is bind-mounted by docker-compose (so generated tools + edits persist
# to the host and don't need a rebuild). CMD runs the same launcher you'd run
# locally; it adds /workspace/app to sys.path itself.
ENV PYTHONUNBUFFERED=1
CMD ["python3", "scripts/harness_ui.py"]
