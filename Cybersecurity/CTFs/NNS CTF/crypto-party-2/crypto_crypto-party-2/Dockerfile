FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim
RUN apt-get update && apt-get install -y socat && rm -rf /var/lib/apt/lists/

WORKDIR /app
COPY . ./
RUN uv sync --locked

ENTRYPOINT ["socat", "TCP-LISTEN:3000,fork,reuseaddr", "EXEC:uv run chall.py"]
