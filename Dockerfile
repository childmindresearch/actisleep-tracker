FROM ghcr.io/astral-sh/uv:python3.11-bookworm

EXPOSE 8051
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8051/health || exit 1

WORKDIR /app

COPY . .

RUN uv sync --no-dev

CMD ["uv", "run", "--no-dev", "actigraphy", "/data"]
