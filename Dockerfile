# multistage build requires at least docker-ce 17.06
FROM ubuntu:18.04 AS builder
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"

# use some custom packages that are too obsolete in official repo
# use node.js from nodesource PPA (for npm packages)
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends\
    python \
    python-pip \
    gnupg \
    wget  && \
    wget https://deb.nodesource.com/setup_10.x --no-check-certificate && \
    bash setup_10.x && \
    apt-get install -y --no-install-recommends\
    nodejs && \
    rm -rf /var/lib/apt/lists/*

# server files will be merely copied from builder
COPY ./server /mergin/server

# build frontend app
COPY ./web-app /mergin/web-app
WORKDIR /mergin/web-app
RUN npm install
RUN npm run build

CMD echo 'Build is finished.'

FROM ubuntu:18.04
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends\
    musl-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    iputils-ping \
    gcc build-essential binutils cmake extra-cmake-modules && \
    rm -rf /var/lib/apt/lists/*


# needed for geodiff
RUN pip3 install --upgrade pip
RUN ln -s /usr/lib/x86_64-linux-musl/libc.so /lib/libc.musl-x86_64.so.1

# create mergin user to run container with
RUN groupadd -r mergin -g 901
RUN groupadd -r mergin-family -g 999
RUN useradd -u 901 -r --home-dir /app --create-home -g mergin -G mergin-family -s /sbin/nologin  mergin

WORKDIR /app
COPY --from=builder /mergin/server .

RUN pip3 install pipenv==2018.11.26
# for locale check this http://click.pocoo.org/5/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN pipenv install --system --deploy

USER mergin
COPY ./entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]