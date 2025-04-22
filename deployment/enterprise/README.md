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
sudo docker pull 433835555346.dkr.ecr.eu-west-1.amazonaws.com/mergin/mergin-ee-back:2025.2.0
```

Then modify [docker-compose file](docker-compose.yml) and most notably settings in `.prod.env` (search for FIXME). Details about configuration can be find in [docs](https://merginmaps.com/docs/server/install/).

```
cp .env.template .prod.env
```

Next step is to create data directory for mergin maps `projects` and `overviews` with proper permissions. This guide assumes data will be stored at  `/mnt/data` directory. Should you prefer a different location, please do search and replace it in config files (`.prod.env`, `docker-compose.yaml`). Make sure your volume is large enough since mergin maps keeps all projects files, their history and also needs some space for temporary processing.

Projects (default `./data`)
```
export MERGIN_DIR=./data
sudo mkdir -p $MERGIN_DIR
sudo find $MERGIN_DIR -type f -exec sudo chmod 640 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod 750 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod g+s {} \;
sudo chown -R 901:999 $MERGIN_DIR
```

Overviews (default `./overviews`)
```
export MERGIN_DIR=./overviews
sudo mkdir -p $MERGIN_DIR
sudo find $MERGIN_DIR -type f -exec sudo chmod 640 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod 750 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod g+s {} \;
sudo chown -R 901:999 $MERGIN_DIR
```

You can use the auxiliary script `set_permissions.sh` in `common` folder for this.
Example, if you using the default `enterprise` deployment folder:

```shell

sh ../common/set_permissions.sh data
sh ../common/set_permissions.sh overviews

```

Once configured, mergin maps can be started (accessible on http://localhost:8080):

## Provision Database and init application

### After version 2025.2.0:
```
sudo docker compose --env-file .prod.env -f docker-compose.yaml up -d
sudo docker exec mergin-server-enterprise flask init --email myuser@mycompany.com
```
Check command output info for database setup and provision, set initial superuser, celery settings and email test.
For more info check [documentation](https://merginmaps.com/docs/server/install/#initialise-database)

Alternatively, you can run the following provisioning commands with some extra steps.

### Prior to version 2025.2.0:
```
sudo docker compose --env-file .prod.env -f docker-compose.yaml up
sudo docker exec mergin-server-enterprise flask init-db
# now create super user account
sudo docker exec mergin-server-enterprise flask user create <username> <password> --is-admin --email <email>
```  

## WebMaps

If you want to deploy MerginMaps Webmaps infrastructure, please adjust `.prod.env` related environment variables and run:
> [!NOTE]
> Please remember the main Mergin Maps stack needs to be running already.
> Otherwise, run it:
> `docker compose --env-file .prod.env -f docker-compose.yaml up -d`

```
 sudo docker compose -f docker-compose.maps.yaml up -d
```

## Install and configure nginx for TLS termination
```
sudo apt update
sudo apt install nginx
```
and get some certificates from let's encrypt
(e.g. see https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-22-04)
```
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d merginmaps.company.com -d www.merginmaps.company.com
```
edit your [ssl-proxy.conf](./ssl-proxy.conf) file with correct paths to certs and reload server. Make it available for nginx and finally, reload the webserver
```
sudo cp ssl-proxy.conf /etc/nginx/sites-available
sudo ln -s /etc/nginx/sites-available/ssl-proxy.conf /etc/nginx/sites-enabled/
sudo systemctl reload nginx
```

### Fix permissions
If nginx is in front of mergin server then it should be owned by 901:nginx-grp or similar (see `/etc/nginx/nginx.conf`)
