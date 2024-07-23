ARG PYTHON_IMAGE=python:3.11.3-slim
FROM $PYTHON_IMAGE

## Create non-root user (arg has to be exported to env for later build stages)
ARG UID=1000
ARG USER=appuser
ENV USER="$USER"
RUN useradd --home-dir /home/$USER --user-group --create-home --uid $UID $USER

## Commands below run relative to this working directory
ARG WORKDIR=/app
WORKDIR $WORKDIR

## Copy Pipfiles into the working directory
COPY ./Pipfile* ./

## Create virtual environment according to Pipfile.lock into user's home as root
RUN HOME=/home/$USER pipenv sync \
    # clean-up
    && rm -rf ~/.cache

## Copy the rest of the application owned by root
COPY ./ ./

## Run as non-root user
USER $USER
