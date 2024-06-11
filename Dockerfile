FROM python:3.11

WORKDIR /code

COPY . /code

COPY .env /code

RUN pip install . 

EXPOSE 80

CMD ["chess-api"]
