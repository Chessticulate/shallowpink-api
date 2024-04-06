import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chessticulate_api.main import app

client = TestClient(app)


class TestLogin:
    
    @pytest.mark.asyncio
    async def test_login_with_bad_credentials(self):
        response = client.post(
            "/login",
            headers={},
            json={"name": "nonexistantuser", "email": "baduser@email.com", "password": "pswd"}
        )
        
        assert response.status_code == 401


    @pytest.mark.asyncio
    async def test_login_succeeds(self):
        response = client.post(
            "/login",
            headers={},
            json={"name": "fakeuser3", "email": "fakeuser3@fakeemail.com", "password": "fakepswd3"}
        )

        assert response.status_code == 200


class TestSignup:

    @pytest.mark.asyncio
    async def test_signup_with_bad_credentials_password_too_short(self):
        response = client.post(
            "/signup",
            headers={},
            json={"name": "baduser", "email": "baduser@email.com", "password": "pswd"}
        )

        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_signup_succeeds(self):
        response = client.post(
            "/signup",
            headers={},
            json={
                "name": "ChessFan12",
                "email": "chessfan@email.com",
                "password": "Knightc3!",
            },
        )
      
        assert response.status_code == 200
        result = response.json()
        assert result is not None and "jwt" in result
        decoded_token = jwt.decode(result["jwt"], options={"verify_signature": False})
        assert decoded_token["user_name"] == "fakeuser3"


class TestGetUser:
    
    @pytest.mark.asyncio
    async def test_get_user_fails_missing_url_params(self):
        response = client.get("/user")
        assert response.status_code == 403 

    @pytest.mark.asyncio
    async def test_get_user_id(self):
        response = client.get("/user?user_id=1")
        assert response.status_code == 200 

    @pytest.mark.asyncio
    async def test_get_user_by_name(self):
        response = client.get("/user?user_name=fakeuser1") 
        assert response.status_code == 200
    
