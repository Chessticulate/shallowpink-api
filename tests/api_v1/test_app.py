from fastapi import FastAPI
from fastapi.testclient import TestClient

# endpoints are in main.py
from chessticulate_api.routers.v1 import app

client = TestClient(app)

def test_login():
    response = client.post(
        "/login",
        headers={},
        json={
            "name": "fakeuser1",
            "password": "password"
        },
    )

    assert response.status_code == 200
