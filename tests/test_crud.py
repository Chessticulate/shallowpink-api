from datetime import datetime, timedelta, timezone

import jwt
import pytest
import sqlalchemy
from pydantic import SecretStr

from chessticulate_api import crud, models
from chessticulate_api.config import CONFIG


def test_password_hashing():
    pswd = SecretStr("test password")

    pswd_hash = crud._hash_password(pswd)

    assert crud._check_password(pswd, pswd_hash)


@pytest.mark.asyncio
async def test_get_user_by_name(init_fake_user_data, fake_user_data):
    # test get user that doesnt exist

    assert await crud.get_user_by_name("baduser") is None

    for data in fake_user_data:
        user = await crud.get_user_by_name(data["name"])
        assert user.email == data["email"]


@pytest.mark.asyncio
async def test_get_user_by_id(init_fake_user_data, fake_user_data):
    # test bad id, not an integer

    assert await crud.get_user_by_id("apple") is None

    id_ = 1
    for data in fake_user_data:
        user = await crud.get_user_by_id(id_)
        id_ += 1
        assert user.name == data["name"]


@pytest.mark.asyncio
async def test_create_user(drop_all_users):
    fake_name = "cleo"
    fake_email = "cleo@dogmail.com"
    fake_password = SecretStr("IloveKongs")

    assert await crud.get_user_by_name(fake_name) is None
    user = await crud.create_user(fake_name, fake_email, fake_password)

    assert user.name == fake_name
    assert user.email == fake_email
    assert crud._check_password(fake_password, user.password)

    # test creating users with duplicate id's emails usernames etc
    # username too long/short, invalid chars

    fake_name2 = "ally"
    fake_email2 = "cleo@dogmail.com"
    fake_pass2 = SecretStr("treats")

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await crud.create_user(fake_name2, fake_email2, fake_pass2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await crud.create_user(fake_name, fake_email, fake_password)


@pytest.mark.asyncio
async def test_login_validate_token(init_fake_user_data):
    # test expired token

    token = await crud.login("fakeuser1", SecretStr("fakepswd1"))
    decoded_token = crud.validate_token(token)
    assert decoded_token["user_name"] == "fakeuser1"

    assert await crud.login("baduser", SecretStr("badpswd")) is None

    with pytest.raises(jwt.exceptions.DecodeError):
        crud.validate_token("nonsense")

    token = jwt.encode(
        {
            "exp": datetime.now(tz=timezone.utc) - timedelta(days=CONFIG.token_ttl),
            "user_name": "fakeuser1",
        },
        CONFIG.secret,
    )

    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        assert crud.validate_token(token) is not None


@pytest.mark.asyncio
async def test_create_invitation(init_fake_user_data):
    # both users must exist for a valid invitation
    assert await crud.create_invitation("fakeuser1", "baduser") is None

    invitation = await crud.create_invitation("fakeuser1", "fakeuser2")

    assert invitation.status.value is models.InvitationStatus.PENDING.value
    assert (await crud.get_user_by_id(invitation.from_)).name == "fakeuser1"
    assert (await crud.get_user_by_id(invitation.to)).name == "fakeuser2"
    assert invitation.game_type.value is models.GameType.CHESS.value


@pytest.mark.asyncio
async def test_get_invitations(init_fake_user_data):
    # invitation cannot be made with non existent users

    invitation = await crud.create_invitation("fakeuser1", "fakeuser2")
    result = await crud.get_invitations(id_=invitation.id_)

    assert result[0].id_ == invitation.id_
    assert result[0].from_ == invitation.from_
    assert result[0].to == invitation.to
    assert result[0].game_type.value == invitation.game_type.value
    assert result[0].status.value == invitation.status.value

    await crud.create_invitation("fakeuser1", "nonexistent")
