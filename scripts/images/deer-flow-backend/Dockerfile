FROM ghcr.io/astral-sh/uv:python3.12-bookworm

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install system dependencies including libpq
RUN apt-get update && apt-get install -y \
    libpq-dev git \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /app

# Copy the application into the container.
RUN git clone https://github.com/bytedance/deer-flow.git /app
COPY runtime/deer-flow/feature_collection.patch /app/feature_collection.patch
COPY runtime/deer-flow/.env /app/.env
COPY runtime/deer-flow/conf.yaml /app/conf.yaml

RUN git apply feature_collection.patch

# Pre-cache the application dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Install the application dependencies.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

# Run the application.
CMD ["uv", "run", "python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
