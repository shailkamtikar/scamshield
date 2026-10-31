# ScamShield API for Render (or any Docker host). Build context: the backend folder.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Tesseract reads text from screenshots; libglib is needed by OpenCV.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# The code expects <root>/backend/app and writes its feed cache to <root>/data/cache.
WORKDIR /app/backend
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/backend/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
RUN mkdir -p /app/data/cache && useradd --create-home runner && chown -R runner /app
USER runner

ENV TRUST_PROXY_HEADERS=true
EXPOSE 10000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips='*'"]
