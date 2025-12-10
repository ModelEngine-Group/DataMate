FROM python:3.12-slim

# Single-stage image with build cache optimization using BuildKit cache mounts.
# Note: to use the cache mount syntax you must build with BuildKit enabled:
# DOCKER_BUILDKIT=1 docker build . -f scripts/images/datamate-python/Dockerfile -t datamate-backend-python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Poetry configuration
    POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Install Poetry via pipx as Poetry officially recommends
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade --root-user-action=ignore pip \
    && pip install --root-user-action=ignore pipx \
    && pipx install "poetry==$POETRY_VERSION"

# Copy only dependency files first (leverages layer caching when dependencies don't change)
COPY runtime/datamate-python/pyproject.toml runtime/datamate-python/poetry.lock* /app/

# Install dependencies using Poetry with cache mount
# --no-root: don't install the project itself yet (only dependencies)
# --only main: only install main dependencies, not dev dependencies
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --no-root --only main

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt_tab', download_dir='/usr/local/nltk_data')"
ENV NLTK_DATA=/usr/local/nltk_data

# Copy the rest of the application
COPY runtime/datamate-python /app

COPY runtime/datamate-python/deploy/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh || true

# Expose the application port
EXPOSE 18000

ENTRYPOINT ["/docker-entrypoint.sh"]
