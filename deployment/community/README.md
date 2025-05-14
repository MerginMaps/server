# Mergin Maps Community Edition Deployment
Suitable for Ubuntu servers, one node deployment using docker compose and system nginx as a reverse proxy.

> [!IMPORTANT] 
> You need to have Docker installed on your system.
> If you don't have, follow the official [documentation](https://docs.docker.com/engine/install/)

Then modify [docker-compose file](docker-compose.yml) and create environment file `.prod.env` from `.env.template`. Details about configuration can be find in [docs](https://merginmaps.com/docs/server/install/).

```shell
cp .env.template .prod.env
```

Next step is to create data directory for mergin maps `projects` with proper permissions. Should you prefer a different location, please do search and replace it in config files (`.prod.env`, `docker-compose.yml`). Make sure your volume is large enough since mergin maps keeps all projects files, their history and also needs some space for temporary processing.

If you want to persist diagnostic logs, create data directory `diagnostic_logs` with proper permissions.

For more details about deployment please check [docs](https://merginmaps.com/docs/server/install/#deployment).
