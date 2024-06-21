FROM ubuntu:focal-20230301
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"

# Set working directory
WORKDIR /app

# this is to do choice of timezone upfront, because when "tzdata" package gets installed,
# it comes up with interactive command line prompt when package is being set up
ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG BUILD_HASH="unknown"
ENV BUILD_HASH=${BUILD_HASH}

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends\
    musl-dev \
    python3 \
    python3-pip \
    python3-setuptools \
    iputils-ping \
    gcc build-essential binutils cmake extra-cmake-modules libsqlite3-mod-spatialite && \
    rm -rf /var/lib/apt/lists/*

# needed for geodiff
RUN pip3 install --upgrade pip
RUN ln -s /usr/lib/x86_64-linux-musl/libc.so /lib/libc.musl-x86_64.so.1

COPY ./Pipfile.lock /app
COPY ./Pipfile /app

RUN pip3 install pipenv==2022.7.24
# for locale check this http://click.pocoo.org/5/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pipenv install --system --deploy --verbose
RUN pip3 install flower==2.0.1

ARG UID=901
ARG GID=901

# create mergin user to run container with
RUN groupadd -r mergin -g "${GID}"
RUN groupadd -r mergin-family -g 999
RUN useradd -u "${UID}" --home-dir /home/mergin/app -r -g mergin -G mergin-family -s /sbin/nologin  mergin

COPY --chown=mergin:mergin . /home/mergin/app
RUN chmod -R 755 /home/mergin/app

# Set the non-root user as the default user
USER mergin

# Set working directory for non root user
WORKDIR /home/mergin/app

ENTRYPOINT ["/home/mergin/app/entrypoint.sh"]
