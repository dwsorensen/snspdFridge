FROM python:3.10
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
     apt-get install -y \
     python3 \
     python3-dev \
     python3-pip \
     python3-pandas \
     python3-scipy \
     libtool pkg-config build-essential autoconf automake \
     libzmq3-dev \
     git \
     && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /app/requirements.txt

COPY /drivers/ /drivers/

ENV PYTHONPATH '/drivers/'

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libusb-1.0-0-dev && \
    chmod 755 /drivers/install_uldaq.sh && \
    /drivers/install_uldaq.sh && \
    python3 -m pip install --upgrade pip && \
    pip3 --no-cache-dir install -r requirements.txt
