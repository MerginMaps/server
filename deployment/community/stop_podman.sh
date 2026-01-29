#!/bin/bash
CONTAINERS="merginmaps-proxy merginmaps-web celery-worker celery-beat merginmaps-server merginmaps-redis merginmaps-db"

echo "Stopping containers..."
# Ignore errors if containers don't exist
podman stop $CONTAINERS 2>/dev/null || true

echo "Removing containers..."
podman rm $CONTAINERS 2>/dev/null || true

# Optional: Remove network
# podman network rm merginmaps 2>/dev/null || true

echo "Stack stopped and removed."
