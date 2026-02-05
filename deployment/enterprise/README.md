# Mergin Maps Enterprise Edition Deployment

Suitable for Ubuntu servers, single-node deployment using Docker Compose and system NGINX as a reverse proxy.

> [!IMPORTANT]
> Docker images for Mergin Maps Enterprise Edition are stored in private Dockerhub repositories.
> To access them, you need a Mergin Maps Enterprise [subscription](https://merginmaps.com/pricing).
> Please contact the Mergin Maps [sales team](https://merginmaps.com/contact-sales)!

## Load Docker Images, Configure, and Run Mergin Maps Stack

Login to dockerhub (you should have already received your access token from Mergin Maps team).
To run Mergin Maps, you need to load local Docker images (if any). Make sure you have access to Lutra's repositories. You can check this by running:

```shell
docker pull lutraconsulting/merginmaps-backend-ee:2025.7.3
```

Then modify the [docker-compose file](docker-compose.yml) and create the environment file `.prod.env` from `.env.template`. Details about configuration can be found in the [docs](https://merginmaps.com/docs/server/install/).

```shell
cp .env.template .prod.env
```

The next step is to create a data directory for Mergin Maps (`data`) with proper permissions. If you prefer a different location, please search and replace it in the configuration files (`.prod.env`, `docker-compose.yml`). Ensure your volume is large enough since Mergin Maps stores all project files, their history, and requires space for temporary processing.

For more details about deployment, please check the [docs](https://merginmaps.com/docs/server/install/#deployment).

### Configure SSO (Optional)

For SSO deployment, you need to run the initialization script:

```shell
cd sso
bash ./sso/sso-init.sh`. 
```

This will generate a ready-to-use file with some pre-generated secrets needed for the SSO backend.  
Alternatively, and most recommended, you can manually create `.sso.env` from the provided `.sso.env.template` and generate your own secret keys as well as other relevant configurations.

Make sure if the proxy has mounted the [./sso/sso-nginx.conf](./sso/sso-nginx.conf) file in the main [docker-compose.yml](./docker-compose.yml) file.

Please follow the Mergin Maps [documentation](https://merginmaps.com/docs/server/sso-deployment/) on this topic.

### Configure WebMaps (Optional)

WebMaps support is activated with the environment variable `MAPS_ENABLED=True` in the main `.prod.env` configuration file.  
Also, check other important WebMaps-related environment variable configurations in the Mergin Maps [docs](https://merginmaps.com/docs/server/environment/#webmaps).

## Run Mergin Maps Stack

Finally, initialize your Mergin Maps stack with:

```shell
docker compose up -d
```

If you have WebMaps enabled, after the main Mergin Maps stack is initialized, simply run:

```shell
docker compose -f docker-compose.sso.yml up -d
# restart merginmaps-proxy nginx in case of any errors with connections
```

The Polis server admin panel will then be available at http://localhost:8081.

If you have WebMaps enabled, after the main Mergin Maps stack is initialized, simply run:

```shell
docker compose -f docker-compose.maps.yml up -d
```

