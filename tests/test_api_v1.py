from fastapi import FastAPI
from fastapi.testclient import TestClient
from chessticulate_api.routers.v1.main import router
import jwt

client = TestClient(router)

def test_login(init_fake_user_data):
    response = client.post(
        "/login",
        headers={},
        json={
            "name": "fakeuser1",
            "password": "fakepswd1"
        },
    )
    resp = response.json()

    assert response.status_code == 200
    assert resp is not None and "jwt" in resp
    decoded_token = jwt.decode(resp["jwt"], options={"verify_signature": False})
    assert decoded_token["user_name"] == "fakeuser1"  
