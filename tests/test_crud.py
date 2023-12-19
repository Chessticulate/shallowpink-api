from app import crud
from app.config import CONFIG
from app.models import ResponseType, GameType
import jwt
import pytest

def test_password_hashing():
    pswd = "test password"

    pswd_hash = crud.hash_password(pswd)
    
    assert crud.check_password(pswd, pswd_hash) 

def test_get_user_by_name(init_fake_user_data, fake_user_data):
    # test get user that doesnt exist

    for data in fake_user_data:
        user = crud.get_user_by_name(data["name"])
        assert user.email == data["email"]

# new
def test_get_user_by_id(init_fake_user_data, fake_user_data):
    # test bad id, not an integer
    id_ = 1
    for data in fake_user_data:
        user = crud.get_user_by_id(id_)
        id_ += 1
        assert user.name == data["name"]

def test_create_user(drop_all_users):
    # test creating users with duplicate id's emails usernames etc
    # username too long/short, invalid chars
    fake_name = "cleo"
    fake_email = "cleo@dogmail.com"
    fake_password = "IloveKongs"

    assert crud.get_user_by_name(fake_name) is None
    crud.create_user(fake_name, fake_email, fake_password)
    user = crud.get_user_by_name(fake_name)

    assert user.name == fake_name
    assert user.email == fake_email
    assert crud.check_password(fake_password, user.password)
    
def test_login_validate_token(init_fake_user_data):
    # test expired token

    token = crud.login("fakeuser1", "fakepswd1")
    decoded_token = crud.validate_token(token)
    assert decoded_token == {"user": "fakeuser1"}

    assert crud.login("baduser", "baduser2") is None

    with pytest.raises(jwt.exceptions.DecodeError):
        crud.validate_token("nonsense")

# new
def test_create_invite(init_fake_user_data):
    # test creating invite with non exitent users
    
    invite = crud.create_invite("fakeuser1", "fakeuser2")

    assert invite.response.value is ResponseType.PENDING.value
    assert crud.get_user_by_id(invite.from_).name == "fakeuser1"
    assert crud.get_user_by_id(invite.to).name == "fakeuser2"
    assert invite.game_type.value is GameType.CHESS.value
    
# new 
def test_get_invite(init_fake_user_data):
    # test getting invite with non existent users

    invitation = crud.create_invite("fakeuser1", "fakeuser2")    
    invite = crud.get_invite(invitation.id)
    
    assert invite.id == invitation.id
    assert invite.from_ == invitation.from_
    assert invite.to == invitation.to
    assert invite.game_type.value == invitation.game_type.value
    assert invite.response.value == invitation.response.value
    
