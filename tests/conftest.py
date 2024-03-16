import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy import delete
from sqlalchemy.orm import Session

from chessticulate_api import config, crud, db, models


@pytest.fixture
def fake_app_secret():
    config.CONFIG.secret = "fake_secret"


@pytest_asyncio.fixture
async def drop_all_users():
    async with db.async_session() as session:
        stmt = delete(models.User)
        await session.execute(stmt)
        await session.commit()


@pytest_asyncio.fixture
async def drop_all_data():
    async with db.async_session() as session:
        del_users = delete(models.User)
        del_invitations = delete(models.Invitation)
        del_games = delete(models.Game)
        await session.execute(del_users)
        await session.execute(del_invitations)
        await session.execute(del_games)
        await session.commit()


@pytest.fixture
def fake_user_data():
    return [
        {
            "name": "fakeuser1",
            "password": "fakepswd1",
            "email": "fakeuser1@fakeemail.com",
        },
        {
            "name": "fakeuser2",
            "password": "fakepswd2",
            "email": "fakeuser2@fakeemail.com",
        },
        {
            "name": "fakeuser3",
            "password": "fakepswd3",
            "email": "fakeuser3@fakeemail.com",
        },
    ]


@pytest.fixture
def fake_game_data():
    return [
        {
            "invitation_id": "1",
            "player_1": "1",
            "player_2": "2",
            "whomst": "1",
        },
        {
            "invitation_id": "2",
            "player_1": "3",
            "player_2": "1",
            "whomst": "3",
        },
        {
            "invitation_id": "3",
            "player_1": "2",
            "player_2": "3",
            "whomst": "2",
        },
    ]


@pytest_asyncio.fixture
async def init_fake_user_data(fake_user_data, drop_all_users, fake_app_secret):
    async with db.async_session() as session:
        for data in fake_user_data:
            pswd = crud._hash_password(SecretStr(data.pop("password")))
            user = models.User(**data, password=pswd)
            session.add(user)
        await session.commit()


@pytest_asyncio.fixture
async def init_fake_game_data(fake_game_data, drop_all_data):
    async with db.async_session() as session:
        for data in fake_game_data:
            game = models.Game(**data)
            session.add(game)
        await session.commit()
