FROM ghcr.io/astral-sh/uv:0.12.3 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONUNBUFFERED=1 UV_NO_CACHE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY workbench/pyproject.toml workbench/uv.lock /app/workbench/
RUN uv sync --project workbench --locked --extra references --no-dev --no-install-project
COPY workbench/src /app/workbench/src
COPY workbench/teaching /app/workbench/teaching
COPY workbench/scripts/serve_workshop.py /app/workbench/scripts/serve_workshop.py
RUN uv sync --project workbench --locked --extra references --no-dev \
    && useradd --uid 10001 --create-home relay \
    && mkdir /data && chown relay:relay /data
USER relay
ENV PATH="/app/workbench/.venv/bin:$PATH" RELAY_DATA_DIR=/data
EXPOSE 8000
CMD ["python", "workbench/scripts/serve_workshop.py"]
