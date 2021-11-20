FROM python:3.7-alpine
MAINTAINER AngaraLtd


ENV PYTHONUNBUFFERED 1
# ENV PYTHONPATH="$PYTHONPATH:/usr/local/bin/"

RUN apk add --no-cache su-exec

COPY ./requirements.txt /requirements.txt

RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev

RUN pip3.7 install -r /requirements.txt

RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN adduser -D user
USER user

