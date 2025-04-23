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
For running mergin maps you need to load local docker images (if any). Make sure you have access to Lutra's ECR repository. You can check it by running
```
sudo docker pull 433835555346.dkr.ecr.eu-west-1.amazonaws.com/mergin/mergin-ee-back:2025.3.0
```

Then modify [docker-compose file](docker-compose.yml) and create environment file `.prod.env` from `.env.template`. Details about configuration can be find in [docs](https://merginmaps.com/docs/server/install/).

```shell
cp .env.template .prod.env
```

Next step is to create data directory for mergin maps `data` with proper permissions. Should you prefer a different location, please do search and replace it in config files (`.prod.env`, `docker-compose.yml`). Make sure your volume is large enough since mergin maps keeps all projects files, their history and also needs some space for temporary processing.

For more details about deployment please check [docs](https://merginmaps.com/docs/server/install/#deployment).

## WebMaps

If you want to deploy MerginMaps Webmaps infrastructure, please adjust `.prod.env` related environment:

```
MAPS_ENABLED=true
```

and run the following command for creating data directory for webmaps:

```
sh ../common/set_permissions.sh map_data
```

> [!NOTE]
> Please remember the main Mergin Maps stack needs to be running already.
> Otherwise, run it:
> `docker compose -f docker-compose.yml up -d`

```shell
 sudo docker compose -f docker-compose.maps.yml up -d
```