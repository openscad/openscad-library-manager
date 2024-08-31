FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y

RUN apt-get install -y --no-install-recommends \
	ca-certificates \
	python3-minimal \
	build-essential \
	libreadline-dev \
	python3-wheel \
	python3-venv \
	python3-dev \
	pkg-config \
	patch \
	git

RUN . /etc/lsb-release ; echo "deb [trusted=yes] https://download.opensuse.org/repositories/home:/t-paul:/libversion/xUbuntu_$DISTRIB_RELEASE/ ./" | tee /etc/apt/sources.list.d/libversion.list

RUN apt-get update && apt-get install -y --no-install-recommends \
	libversion3-dev

RUN mkdir /olman

WORKDIR /olman

RUN git clone https://github.com/openscad/openscad-library-manager.git .

RUN python3 -m venv .venv

RUN . .venv/bin/activate ; pip install build wheel
RUN . .venv/bin/activate ; pip install pyinstaller rich readline
RUN . .venv/bin/activate ; cd olman-models && pip install .
RUN . .venv/bin/activate ; cd olman-vcs-utils && pip install .
RUN . .venv/bin/activate ; cd olman-version-utils && pip install .
RUN . .venv/bin/activate ; cd olman-client && pip install .
RUN . .venv/bin/activate ; cd olman-cli && pip install .
