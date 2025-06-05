# Mergin Maps Enterprise Edition Deployment
Suitable for Ubuntu servers, one node deployment using docker compose and system nginx as a reverse proxy.

> [!IMPORTANT] 
> Docker images for Mergin Maps Enterprise edition are stored on a private AWS ECR repository.
> To access them, you need a Mergin Maps Enterprise [subscription](https://merginmaps.com/pricing).
> Please contact Mergin Maps [sales team](https://merginmaps.com/contact-sales)!

## Login to Mergin Maps AWS ECR repository
```shell
aws ecr --region eu-west-1 get-login-password | docker login --username AWS --password-stdin 433835555346.dkr.ecr.eu-west-1.amazonaws.com
```

## Load docker images, configure and run mergin maps stack
For running Mergin Maps you need to load local docker images (if any). Make sure you have access to Lutra's ECR repository. You can check it by running
```
docker pull 433835555346.dkr.ecr.eu-west-1.amazonaws.com/mergin/mergin-ee-back:2025.3.0
```

Then modify [docker-compose file](docker-compose.yml) and create environment file `.prod.env` from `.env.template`. Details about configuration can be find in [docs](https://merginmaps.com/docs/server/install/).

```shell
cp .env.template .prod.env
```

Next step is to create data directory for Mergin Maps `data` with proper permissions. Should you prefer a different location, please do search and replace it in config files (`.prod.env`, `docker-compose.yml`). Make sure your volume is large enough since Mergin Maps keeps all projects files, their history and also needs some space for temporary processing.

For more details about deployment please check [docs](https://merginmaps.com/docs/server/install/#deployment).

Finally initialize your Mergin Maps stack with:

```shell
docker compose up -d
```

# WebMaps

Webmaps support is activate with environment variable `MAPS_ENABLED=True` on the main `.prod.env` configuration file.
Also check other important webmaps related environment variables configurations on Mergin Maps [docs](https://merginmaps.com/docs/server/environment/#webmaps)


If you have it enabled, after the normal Mergin Maps stack is initialized simply run:

```shell
docker compose -f docker-compose.maps.yml up -d
```

# SSO

For SSO deployment, first you need to change some relevant content on the provide `.sso.env.template` file, namely the default values on the following environment variable: (`NEXTAUTH_ADMIN_CREDENTIALS, RETRACED_ADMIN_ROOT_TOKEN, NEXTAUTH_ACL`).

Next, under folder `sso-connections` run the initialization script `sso-init.sh`. This will generate a ready to use file with some pregenerated secrets needed for the sso backend. If you want, and it's actually advised, you can create/generate your own secrets.

Before the deployment, check that SSO related environment variables, namely `SSO_ENABLE=True`, are set.
Please follow Mergin Maps [documentation](https://merginmaps.com/docs/server/environment/#sso) on this topic.

Finally simply run the SSO stack with:

```shell
docker compose -f docker-compose.sso.yml up -d
```