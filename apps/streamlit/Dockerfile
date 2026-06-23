FROM python:3.13-slim-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/apps/streamlit

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY apps/streamlit ./apps/streamlit
COPY apps/streamlit/.streamlit ./.streamlit

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "apps/streamlit/dashboards/marketing.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true", "--client.toolbarMode", "viewer", "--browser.gatherUsageStats", "false"]
