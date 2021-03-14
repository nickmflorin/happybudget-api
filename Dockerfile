FROM python:3.8.8-slim
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev musl-dev \
    libcurl4-openssl-dev libssl-dev libpq-dev nano curl

RUN mkdir /app
WORKDIR /app

COPY README.md poetry.lock pyproject.toml /app/
COPY .env /app/

RUN pip --default-timeout=1000 install -U pip setuptools wheel poetry
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip --default-timeout=1000 install -r requirements.txt
RUN pip install python-dateutil

ADD src /app/

RUN ls -alh

EXPOSE 8000