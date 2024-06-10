FROM python:3.9

WORKDIR /code

COPY ./pyproject.toml /code/pyproject.toml

COPY . /code

RUN pip install --no-cache-dir -e .[dev]

CMD ["fastapi", "run", "chessticulate_api/__main__.py", "--port", "80"]
