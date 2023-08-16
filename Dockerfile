FROM python:3.10-slim-bullseye as base

ENV PYTHONUNBUFFERED 1

RUN apt update && apt install git -y

RUN pip install poetry==1.5.1

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry export --without-hashes --with dev --output=requirements.txt
RUN pip install -r requirements.txt


COPY . /app
RUN chmod +x docker/start.sh
RUN chmod +x docker/scheduler.sh
ENTRYPOINT [ "docker/start.sh" ]