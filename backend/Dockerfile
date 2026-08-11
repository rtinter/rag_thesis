FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Torch-Variante: cpu (Standard, ~2 GB) oder gpu (CUDA, ~12 GB).
# Wird von den Compose-Dateien ueber build.args gesetzt.
ARG TORCH_VARIANT=cpu

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_HTTP_TIMEOUT=600 

WORKDIR /srv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --extra ${TORCH_VARIANT}

COPY app ./app
COPY scripts ./scripts

ENV PATH="/srv/.venv/bin:$PATH"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]