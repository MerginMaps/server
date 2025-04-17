# Mergin Maps Community Edition Deployment
Suitable for Ubuntu servers, one node deployment using docker compose and system nginx as a reverse proxy.

> [!IMPORTANT] 
> You need to have Docker installed on your system.
> If you don't have, follow the official [documentation](https://docs.docker.com/engine/install/)

Then modify [docker-compose file](docker-compose.yml) and most notably settings in `.prod.env` (search for FIXME). Details about configuration can be find in [docs](https://merginmaps.com/docs/server/install/).

```
cp .env.template .prod.env
```

Next step is to create data directory for mergin maps `projects` with proper permissions. This guide assumes data will be stored at  `/mnt/data` directory. Should you prefer a different location, please do search and replace it in config files (`.prod.env`, `docker-compose.yaml`). Make sure your volume is large enough since mergin maps keeps all projects files, their history and also needs some space for temporary processing.

Projects (default `./projects`)
```
export MERGIN_DIR=./projects
sudo mkdir -p $MERGIN_DIR
sudo find $MERGIN_DIR -type f -exec sudo chmod 640 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod 750 {} \;
sudo find $MERGIN_DIR -type d -exec sudo chmod g+s {} \;
sudo chown -R 901:999 $MERGIN_DIR
```

You can use the auxiliary script `set_permissions.sh` in `common` folder for this.
Example, if you using the default `community` deployment folder:

```shell

sh deployment/community/check_permission.sh deployment/community/projects

```

Once configured, mergin maps can be started (accessible on http://localhost:8080):

## Provision Database and init application

```
sudo docker compose --env-file .prod.env -f docker-compose.yaml up -d
sudo docker exec mergin-server-enterprise flask init --email myuser@mycompany.com
```
Check command output info for database setup and provision, set initial superuser, celery settings and email test.
For more info check [documentation](https://merginmaps.com/docs/server/install/#initialise-database)

Alternatively, you can run the following provisioning commands with some extra steps.

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
