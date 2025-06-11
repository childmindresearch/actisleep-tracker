FROM ghcr.io/astral-sh/uv:python3.11-bookworm

EXPOSE 8051

WORKDIR /app

COPY . .

RUN uv sync

CMD ["uv", "run", "actigraphy", "/data"]
