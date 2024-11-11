FROM python:3.10
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
     apt-get install -y \
     python3 \
     python3-dev \
     python3-pip \
     libtool pkg-config build-essential autoconf automake \
     libzmq3-dev \
     git \
     && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt

COPY taggerInstall.deb /app/taggerInstall.deb

WORKDIR /app

RUN apt-get update && \
    python3 -m pip install --upgrade pip && \
    pip3 --no-cache-dir install -r requirements.txt 
    
    
RUN apt-get install liblua5.3-0 && \
     dpkg -i taggerInstall.deb
