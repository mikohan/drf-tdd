FROM python:3.7-alpine
MAINTAINER AngaraLtd


ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt


RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN pip install flake8
RUN flake8 --ignore=E501,F401 ./app

RUN adduser -D user
USER user
