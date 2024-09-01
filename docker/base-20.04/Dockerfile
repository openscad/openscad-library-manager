FROM ubuntu:20.04

ARG PYTHON_VERSION=3.12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y --no-install-recommends wget gpg ca-certificates software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa -y

RUN wget -qO - https://files.openscad.org/OBS-Repository-Key.pub | gpg --dearmor -o /etc/apt/trusted.gpg.d/obs-openscad.gpg

RUN . /etc/lsb-release ; echo "deb https://download.opensuse.org/repositories/home:/t-paul:/libversion/xUbuntu_$DISTRIB_RELEASE/ ./" | tee /etc/apt/sources.list.d/libversion.list

RUN apt-get update

RUN apt-get install -y --no-install-recommends \
	python$PYTHON_VERSION-minimal \
	python$PYTHON_VERSION-venv \
	python$PYTHON_VERSION-dev \
	build-essential \
	libversion3-dev \
	pkg-config \
	patch \
	git

RUN mkdir /olman

WORKDIR /olman

RUN git clone https://github.com/openscad/openscad-library-manager.git .

RUN python$PYTHON_VERSION -m venv .venv

RUN . .venv/bin/activate ; pip install build wheel
RUN . .venv/bin/activate ; pip install pyinstaller
RUN . .venv/bin/activate ; cd olman-models && pip install .
RUN . .venv/bin/activate ; cd olman-vcs-utils && pip install .
RUN . .venv/bin/activate ; cd olman-version-utils && pip install .
RUN . .venv/bin/activate ; cd olman-client && pip install .
RUN . .venv/bin/activate ; cd olman-cli && pip install .
