FROM ubuntu:noble-20251013
MAINTAINER Martin Varga "martin.varga@lutraconsulting.co.uk"

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
    gcc build-essential binutils cmake extra-cmake-modules libsqlite3-mod-spatialite libmagic1 && \
    rm -rf /var/lib/apt/lists/*

# create mergin user to run container with
RUN groupadd -r mergin -g 901
RUN groupadd -r mergin-family -g 999
RUN useradd -u 901 -r --home-dir /app --create-home -g mergin -G mergin-family -s /sbin/nologin  mergin

# copy app files
COPY . /app
WORKDIR /app

# keep installing to system packages
ENV PIP_BREAK_SYSTEM_PACKAGES=1
ENV PIP_IGNORE_INSTALLED=1

RUN pip install pipenv==2026.0.3
# for locale check this http://click.pocoo.org/5/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pipenv install --system --deploy --verbose --python 3.12

USER mergin

COPY ./entrypoint.sh .
ENTRYPOINT ["/app/entrypoint.sh"]
