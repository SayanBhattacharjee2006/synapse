FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# This is a Docker feature called multi-stage copy. It copies a file from another Docker image directly into your image without running that image as a container.

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml .
COPY uv.lock* .

RUN uv sync --frozen --no-dev

COPY . .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]