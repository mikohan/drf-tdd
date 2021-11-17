FROM python:3.7-stretch
MAINTAINER AngaraLtd


ENV PYTHONUNBUFFERED 1
ENV PATH "$PATH:/home/user/.local/bin"

RUN mkdir  /app
WORKDIR /app
COPY ./app /app

RUN adduser -D user
USER user




COPY  ./requirements.txt /requirements.txt
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --user -r /requirements.txt



