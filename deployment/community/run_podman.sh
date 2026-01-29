#!/bin/bash
set -e

NETWORK="merginmaps"

# Create network if it doesn't exist
if ! podman network exists $NETWORK; then
    echo "Creating network $NETWORK..."
    podman network create $NETWORK
fi

# Function to run a container if it doesn't exist (optional cleanup can be added)
# For now, we assume this script starts the stack. Users should `podman rm -f` manually to restart.

echo "Starting Database..."
podman run -d \
    --name merginmaps-db \
    --network $NETWORK \
    --network-alias db \
    --restart always \
    -e POSTGRES_DB=mergin \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -v ./mergin_db:/var/lib/postgresql/data \
    postgres:14

echo "Starting Redis..."
podman run -d \
    --name merginmaps-redis \
    --network $NETWORK \
    --network-alias redis \
    --restart always \
    redis:6.2.17

echo "Starting Server..."
# Note: Ensure .prod.env exists or provided variables match production requirements
podman run -d \
    --name merginmaps-server \
    --network $NETWORK \
    --network-alias server \
    --restart always \
    --user 901:999 \
    -v ./projects:/data \
    -v ./diagnostic_logs:/diagnostic_logs \
    --env-file .prod.env \
    lutraconsulting/merginmaps-backend:2025.7.3 \
    gunicorn --config config.py application:application

echo "Starting Celery Beat..."
podman run -d \
    --name celery-beat \
    --network $NETWORK \
    --network-alias celery-beat \
    --restart always \
    --env-file .prod.env \
    -e GEVENT_WORKER=0 \
    -e NO_MONKEY_PATCH=1 \
    lutraconsulting/merginmaps-backend:2025.7.3 \
    celery -A application.celery beat --loglevel=info

echo "Starting Celery Worker..."
podman run -d \
    --name celery-worker \
    --network $NETWORK \
    --network-alias celery-worker \
    --restart always \
    --user 901:999 \
    --env-file .prod.env \
    -e GEVENT_WORKER=0 \
    -e NO_MONKEY_PATCH=1 \
    -v ./projects:/data \
    lutraconsulting/merginmaps-backend:2025.7.3 \
    celery -A application.celery worker --loglevel=info

echo "Starting Web..."
podman run -d \
    --name merginmaps-web \
    --network $NETWORK \
    --network-alias web \
    --restart always \
    --user 101:999 \
    lutraconsulting/merginmaps-frontend:2025.7.3

echo "Starting Proxy..."
podman run -d \
    --name merginmaps-proxy \
    --network $NETWORK \
    --network-alias proxy \
    --restart always \
    --user 101:999 \
    -p 8080:8080 \
    -v ./projects:/data \
    -v ../common/nginx.conf:/etc/nginx/conf.d/default.conf \
    nginxinc/nginx-unprivileged:1.27

echo "Stack started successfully with Podman."
