FROM python:3.11-slim

# Single-stage image with build cache optimization using BuildKit cache mounts.
# Note: to use the cache mount syntax you must build with BuildKit enabled:
# DOCKER_BUILDKIT=1 docker build . -f scripts/images/datamate-python/Dockerfile -t datamate-backend-python

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install build deps needed to compile some wheels. We'll remove them afterwards to keep the
# final image small. Use --no-install-recommends to minimize installed packages.
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         build-essential \
#         gcc \
#     && apt-get purge -y --auto-remove build-essential gcc \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first (leverages layer caching when requirements don't change)
COPY runtime/datamate-python /app

# Install Python deps. Use BuildKit cache mount for pip cache to speed subsequent builds.
# The --mount=type=cache requires BuildKit. This keeps downloaded wheels/cache out of the final image.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade --root-user-action=ignore pip setuptools wheel \
    && pip install --root-user-action=ignore -r /app/requirements.txt

COPY runtime/datamate-python/deploy/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh || true

# Expose the application port
EXPOSE 18000

ENTRYPOINT ["/docker-entrypoint.sh"]