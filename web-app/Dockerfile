FROM node:18-alpine as builder
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"

# build frontend apps
COPY . /mergin/web-app
WORKDIR /mergin/web-app
RUN yarn install --frozen-lockfile
RUN yarn link:dependencies
RUN yarn build:all
RUN PUBLIC_PATH=/admin/ yarn build:all:admin

FROM nginx:alpine
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"
WORKDIR /usr/share/nginx/html
# client app
COPY --from=builder /mergin/web-app/packages/app/dist ./app
# admin app
COPY --from=builder /mergin/web-app/packages/admin-app/dist ./admin
# basic nginx config to serve static files
COPY ./nginx.proxy.conf /etc/nginx/conf.d/default.conf
ENTRYPOINT ["nginx", "-g", "daemon off;"]
