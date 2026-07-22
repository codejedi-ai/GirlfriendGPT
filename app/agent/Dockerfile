FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . ./

ENV PYTHONPATH=/app
ENV TOOLS_CATALOG_PATH=/app/tools

CMD ["uv", "run", "python", "voice_agent.py", "dev"]
