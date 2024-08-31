FROM olman-base as builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /olman

RUN ls -la

COPY olman.py olman-cli

RUN . .venv/bin/activate ; cd olman-cli && pyinstaller olman.py --onefile

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y && apt-get clean

RUN mkdir /app

WORKDIR /app

COPY --from=builder /olman/olman-cli/dist/olman .
