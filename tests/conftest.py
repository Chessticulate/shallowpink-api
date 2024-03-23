import pytest
import pytest_asyncio
from copy import copy
from pydantic import SecretStr
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from chessticulate_api import config, crud, db, models


FAKE_USER_DATA = [
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


FAKE_INVITATION_DATA = [
    {
        "from_id": 1,
        "to_id": 2,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.ACCEPTED,
    },
    {
        "from_id": 3,
        "to_id": 1,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.ACCEPTED,
    },
    {
        "from_id": 2,
        "to_id": 3,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.ACCEPTED,
    },
    {
        "from_id": 1,
        "to_id": 2,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.PENDING,
    },
    {
        "from_id": 1,
        "to_id": 2,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.CANCELLED,
    },
    {
        "from_id": 1,
        "to_id": 2,
        "game_type": models.GameType.CHESS,
        "status": models.InvitationStatus.DECLINED,
    },
]


FAKE_GAME_DATA = [
    {
        "invitation_id": 1,
        "player_1": 1,
        "player_2": 2,
        "whomst": 1,
    },
    {
        "invitation_id": 2,
        "player_1": 3,
        "player_2": 1,
        "whomst": 3,
    },
    {
        "invitation_id": 3,
        "player_1": 2,
        "player_2": 3,
        "whomst": 2,
    },
]


@pytest.fixture
def fake_app_secret(scope="session", autouse=True):
    config.CONFIG.secret = "fake_secret"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def sqlite_enforce_foreign_keys():
    async with db.async_session() as session:
        await session.execute(text("PRAGMA foreign_keys = ON;"))
        await session.commit()


@pytest.fixture
def fake_user_data():
    return copy(FAKE_USER_DATA)


@pytest.fixture
def fake_invitation_data(scope="session"):
    return copy(FAKE_INVITATION_DATA)


@pytest.fixture
def fake_game_data(scope="session"):
    return copy(FAKE_GAME_DATA)


async def _init_fake_data():
    async with db.async_session() as session:
        for data in FAKE_USER_DATA:
            data_copy = data.copy()
            pswd = crud._hash_password(SecretStr(data_copy.pop("password")))
            user = models.User(**data_copy, password=pswd)
            session.add(user)
        for data in FAKE_INVITATION_DATA:
            invitation = models.Invitation(**data)
            session.add(invitation)
        for data in FAKE_GAME_DATA:
            game = models.Game(**data)
            session.add(game)
        await session.commit()


async def _drop_all_data():
    db.async_engine = db.create_async_engine(
        config.CONFIG.conn_str, echo=config.CONFIG.sql_echo
    )
    db.async_session = db.async_sessionmaker(db.async_engine, expire_on_commit=False)
    await models.init_db()


@pytest_asyncio.fixture
async def drop_all_data():
    await _drop_all_data()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_fake_data():
    await _init_fake_data()


@pytest_asyncio.fixture
async def restore_fake_data_after():
    yield
    await _drop_all_data()
    await _init_fake_data()
