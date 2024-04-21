import jwt
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from chessticulate_api import crud
from chessticulate_api.main import app

client = AsyncClient(app=app, base_url="http://test")


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_with_bad_credentials(self):
        response = await client.post(
            "/login",
            headers={},
            json={
                "name": "nonexistantuser",
                "email": "baduser@email.com",
                "password": "pswd",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self):
        response = await client.post(
            "/login", headers={}, json={"name": "fakeuser4", "password": "wrongpswd1"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_succeeds(self):
        response = await client.post(
            "/login",
            headers={},
            json={
                "name": "fakeuser3",
                "email": "fakeuser3@fakeemail.com",
                "password": "fakepswd3",
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result is not None and "jwt" in result


class TestSignup:
    @pytest.mark.asyncio
    async def test_signup_with_bad_credentials_password_too_short(self):
        response = await client.post(
            "/signup",
            headers={},
            json={"name": "baduser", "email": "baduser@email.com", "password": "pswd"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_signup_fails_username_already_exists(self):
        response = await client.post(
            "/signup",
            headers={},
            json={
                "name": "fakeuser1",
                "email": "baduser@email.com",
                "password": "F@kepswd420",
            },
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_succeeds(self, restore_fake_data_after):
        response = await client.post(
            "/signup",
            headers={},
            json={
                "name": "ChessFan12",
                "email": "chessfan@email.com",
                "password": "Knightc3!",
            },
        )

        assert response.status_code == 201
        result = response.json()
        assert result is not None
        # decoded_token = jwt.decode(result["jwt"], options={"verify_signature": False})
        assert result["name"] == "ChessFan12"
        assert result["email"] == "chessfan@email.com"
        assert result["password"] != "Knightc3!"


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, token):
        response = await client.get(
            "/users?user_id=1", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        user = response.json()[0]
        assert user["id_"] == 1
        assert user["name"] == "fakeuser1"
        assert user["email"] == "fakeuser1@fakeemail.com"
        assert user["wins"] == user["draws"] == user["losses"] == 0

    @pytest.mark.asyncio
    async def test_get_user_by_name(self, token):
        response = await client.get(
            "/users?user_name=fakeuser2", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 1
        user = users[0]
        assert user["id_"] == 2
        assert user["name"] == "fakeuser2"
        assert user["email"] == "fakeuser2@fakeemail.com"
        assert user["wins"] == user["draws"] == user["losses"] == 0

    @pytest.mark.asyncio
    async def test_get_user_default_params(self, token):
        response = await client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 6

    @pytest.mark.asyncio
    async def test_get_user_custom_params(self, token):
        params = {"skip": 3, "limit": 3, "order_by": "wins"}
        response = await client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}, params=params
        )

        # params are being passed correctly, but I dont think they are all being used
        # reverse and order_by are not working. need to double check get_user crud function
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 3


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_delete_user_fails_not_logged_in(self):
        response = await client.delete("/users/delete")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_user(self, token, restore_fake_data_after):
        response = await client.delete(
            "/users/delete", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204


class TestCreateInvitation:
    @pytest.mark.asyncio
    async def test_creste_invitation_fails_deleted_recipient(self, token):
        response = await client.post(
            "/invitations",
            headers={"Authorization": f"Bearer {token}"},
            json={"to_id": 4, "game_type": "CHESS"},
        )

        assert response.status_code == 400
