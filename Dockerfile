FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.17 /uv /bin

RUN apt-get update && apt-get install -y \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

WORKDIR /app
RUN uv sync --frozen --no-cache

ENTRYPOINT [ "uv", "run", "app.py", "monitor"]
CMD ["/app/config/monitoring_config.yaml"]
