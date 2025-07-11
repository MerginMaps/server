#!/bin/bash
set -eu

# Create sso env file
grep -v '^#' ../.sso.env.template > ../.sso.env
# create key pair for sso if not present
if [[ ! -f key.pem ]] || [[ ! -f public.crt ]]; then
  echo "Generating certificates for sso server..."
  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out public.crt -sha256 -days 365 -nodes -batch
fi


# generate some random secrets
API_KEY=$(openssl rand -base64 32)
echo JACKSON_API_KEYS=$API_KEY >> ../.sso.env
echo DB_ENCRYPTION_KEY=$(openssl rand -base64 32) >> ../.sso.env
echo DB_ENCRYPTION_KEY=$(openssl rand -base64 32) >> ../.sso.env
echo NEXTAUTH_SECRET=$(openssl rand -base64 32) >> ../.sso.env
echo PUBLIC_KEY=$(cat public.crt | base64 | tr -d '\n')  >> ../.sso.env
echo PRIVATE_KEY=$(cat key.pem | base64 | tr -d '\n')  >> ../.sso.env

# mergin maps related env variables
echo SSO_SERVER_API_KEY=$API_KEY >> ../.prod.env
echo SSO_SERVER_INTERNAL_URL=http://merginmaps-proxy:8081 >> ../.prod.env
echo SSO_SERVER_API_URL=http://merginmaps-proxy:8081 >> ../.prod.env
