FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY livekit_token.py voice_sessions.py companions.py main.py ./
COPY static ./static

ENV PYTHONPATH=/app
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8080

EXPOSE 8080

CMD ["uv", "run", "python", "main.py"]
