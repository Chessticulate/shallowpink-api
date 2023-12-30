from app import crud
from app.config import CONFIG
from app.models import ResponseType, GameType
from datetime import datetime, timezone, timedelta
import jwt
import pytest
import sqlalchemy
from pydantic import SecretStr


def test_password_hashing():
    pswd = SecretStr("test password")

    pswd_hash = crud.hash_password(pswd)

    assert crud.check_password(pswd, pswd_hash)


def test_get_user_by_name(init_fake_user_data, fake_user_data):
    # test get user that doesnt exist

    assert crud.get_user_by_name("baduser") is None

    for data in fake_user_data:
        user = crud.get_user_by_name(data["name"])
        assert user.email == data["email"]


# new
def test_get_user_by_id(init_fake_user_data, fake_user_data):
    # test bad id, not an integer

    assert crud.get_user_by_id("apple") is None

    id_ = 1
    for data in fake_user_data:
        user = crud.get_user_by_id(id_)
        id_ += 1
        assert user.name == data["name"]


def test_create_user(drop_all_users):
    fake_name = "cleo"
    fake_email = "cleo@dogmail.com"
    fake_password = SecretStr("IloveKongs")

    assert crud.get_user_by_name(fake_name) is None
    user = crud.create_user(fake_name, fake_email, fake_password)

    assert user.name == fake_name
    assert user.email == fake_email
    assert crud.check_password(fake_password, user.password)

    # test creating users with duplicate id's emails usernames etc
    # username too long/short, invalid chars

    fake_name2 = "ally"
    fake_email2 = "cleo@dogmail.com"
    fake_pass2 = SecretStr("treats")

    with pytest.raises(sqlalchemy.exc.IntegrityError):
        crud.create_user(fake_name2, fake_email2, fake_pass2)
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        crud.create_user(fake_name, fake_email, fake_password)


def test_login_validate_token(init_fake_user_data):
    # test expired token

    token = crud.login("fakeuser1", SecretStr("fakepswd1"))
    decoded_token = crud.validate_token(token)
    assert decoded_token["user"] == "fakeuser1"

    assert crud.login("baduser", SecretStr("badpswd")) is None

    with pytest.raises(jwt.exceptions.DecodeError):
        crud.validate_token("nonsense")

    token = jwt.encode(
        {
            "exp": datetime.now(tz=timezone.utc) - timedelta(days=CONFIG.token_ttl),
            "user": "fakeuser1",
        },
        CONFIG.secret,
    )

    with pytest.raises(jwt.exceptions.ExpiredSignatureError):
        assert crud.validate_token(token) is not None


# new
def test_create_invite(init_fake_user_data):
    # both users must exist for a valid invite
    assert crud.create_invite("fakeuser1", "baduser") is None

    invite = crud.create_invite("fakeuser1", "fakeuser2")

    assert invite.response.value is ResponseType.PENDING.value
    assert crud.get_user_by_id(invite.from_).name == "fakeuser1"
    assert crud.get_user_by_id(invite.to).name == "fakeuser2"
    assert invite.game_type.value is GameType.CHESS.value


# new
def test_get_invite(init_fake_user_data):
    # invitation cannot be made with non existent users

    # get_invite accepts int id
    assert crud.get_invite("id") is None

    invitation = crud.create_invite("fakeuser1", "fakeuser2")
    invite = crud.get_invite(invitation.id)

    assert invite.id == invitation.id
    assert invite.from_ == invitation.from_
    assert invite.to == invitation.to
    assert invite.game_type.value == invitation.game_type.value
    assert invite.response.value == invitation.response.value
