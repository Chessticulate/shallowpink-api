# syntax = docker/dockerfile:1.2
FROM python:3.11

WORKDIR /code

COPY . /code

RUN pip install . 

EXPOSE 80

CMD ["chess-api"]
