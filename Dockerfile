# syntax = docker/dockerfile:1.2
FROM python:3.11

WORKDIR /code

COPY . /code

RUN pip install . 

EXPOSE 80

# ENV APP_HOST=$APP_HOST
# ENV APP_PORT=$APP_PORT
# ENV JWT_SECRET=$JWT_SECRET

CMD ["chess-api"]
