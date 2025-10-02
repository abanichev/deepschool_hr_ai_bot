FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .
COPY app.py .

RUN uv sync

CMD ["uv", "run", "app.py"]
