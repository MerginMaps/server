FROM ubuntu:jammy-20240627.1
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
    gcc build-essential binutils cmake extra-cmake-modules libsqlite3-mod-spatialite && \
    rm -rf /var/lib/apt/lists/*


# needed for geodiff
RUN pip3 install --upgrade pip==24.0

# create mergin user to run container with
RUN groupadd -r mergin -g 901
RUN groupadd -r mergin-family -g 999
RUN useradd -u 901 -r --home-dir /app --create-home -g mergin -G mergin-family -s /sbin/nologin  mergin

# copy app files
COPY . /app
WORKDIR /app

RUN pip3 install pipenv==2024.0.1
# for locale check this http://click.pocoo.org/5/python3/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pipenv install --system --deploy --verbose

USER mergin

COPY ./entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
