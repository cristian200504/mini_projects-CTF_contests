FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim@sha256:d1e005e6f5aac724b7554db95f1c128a77d8d35b59ebe70e188852b4bdad3a3d
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
COPY ca.py names.py app.py ./
COPY templates/ ./templates/
EXPOSE 3000
CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
