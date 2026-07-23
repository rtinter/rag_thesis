FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim 

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1

WORKDIR /srv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY app.py api.py components.py formatting.py theme.css ./
COPY .streamlit ./.streamlit

ENV PATH="/srv/.venv/bin:$PATH"

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
