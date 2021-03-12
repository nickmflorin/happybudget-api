FROM python:3.8.8-slim

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev musl-dev \
    libcurl4-openssl-dev libssl-dev nano curl

RUN mkdir /code
WORKDIR /code

COPY README.md poetry.lock pyproject.toml /code/
COPY .env /code/

RUN pip --default-timeout=1000 install -U pip setuptools wheel poetry
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-root --no-dev

ADD . /code/

RUN ls -alh

EXPOSE 8000