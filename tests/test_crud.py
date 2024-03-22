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


class TestGetUserByName:

    @pytest.mark.asyncio
    async def test_get_user_by_name_does_not_exist(self, init_fake_user_data):
        user = await crud.get_user_by_name("nonexistentuser")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_name_succeeds(self, init_fake_user_data, fake_user_data):
        for user_data in fake_user_data:
            user = await crud.get_user_by_name(user_data["name"])
            assert user is not None
            assert user.name == user_data["name"]


class TestGetUserById:

    @pytest.mark.asyncio
    async def test_get_user_by_id_does_not_exist(self, init_fake_user_data):
        user = await crud.get_user_by_id("4")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_succeeds(self, init_fake_user_data, fake_user_data):
        for user_data in fake_user_data:
            # don't want to assume fakeuser1's ID will be '1' since that technically
            # isn't up to us, so query for user by name first, and use the ID we get
            # back
            user_by_name = await crud.get_user_by_name(user_data["name"])
            user_by_id = await crud.get_user_by_id(user_by_name.id_)
            assert user_by_id.name == user_by_name.name


class TestCreateUser:

    @pytest.mark.asyncio
    async def test_create_user_fails_duplicate_name(self, init_fake_user_data, fake_user_data):
        for user_data in fake_user_data:
            with pytest.raises(sqlalchemy.exc.IntegrityError):
                await crud.create_user(user_data["name"], "unique@fakeemail.com", SecretStr(user_data["password"]))

    @pytest.mark.asyncio
    async def test_create_user_fails_duplicate_email(self, init_fake_user_data, fake_user_data):
        for user_data in fake_user_data:
            with pytest.raises(sqlalchemy.exc.IntegrityError):
                await crud.create_user("unique", user_data["email"], SecretStr(user_data["password"]))

    @pytest.mark.asyncio
    async def test_create_user_succeeds(self, init_fake_user_data):
        user = await crud.create_user("unique", "unique@fakeemail.com", SecretStr("password"))
        assert user is not None
        assert user.name == "unique"
        assert user.email == "unique@fakeemail.com"


class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_delete_user_fails_does_not_exist(self, init_fake_user_data):
        assert await crud.delete_user(42069) == False

    @pytest.mark.asyncio
    async def test_delete_user_succeeds_and_cant_be_deleted_again(self, init_fake_user_data, fake_user_data):
        user = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert user is not None
        assert await crud.delete_user(user.id_) is True
        assert await crud.get_user_by_name(user.name) is None
        assert await crud.delete_user(user.id_) is False


class TestLogin:

    @pytest.mark.asyncio
    async def test_login_fails_user_does_not_exist(self, init_fake_user_data):
        token = await crud.login("doesnotexist", SecretStr("password"))
        assert token is None

    @pytest.mark.asyncio
    async def test_login_fails_bad_password(self, init_fake_user_data, fake_user_data):
        token = await crud.login(fake_user_data[0]["name"], SecretStr("wrongpassword"))
        assert token is None

    @pytest.mark.asyncio
    async def test_login_fails_user_deleted(self, init_fake_user_data, fake_user_data):
        user = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert user is not None
        assert await crud.delete_user(user.id_) is True
        token = await crud.login(fake_user_data[0]["name"], fake_user_data[0]["password"])
        assert token is None

    @pytest.mark.asyncio
    async def test_login_succeeds(self, init_fake_user_data, fake_user_data):
        token = await crud.login(fake_user_data[0]["name"], SecretStr(fake_user_data[0]["password"]))
        assert token is not None


class TestValidateToken:

    @pytest.mark.asyncio
    async def test_validate_token_fails_bad_token(self):
        with pytest.raises(jwt.exceptions.DecodeError):
            crud.validate_token("nonsense")

    @pytest.mark.asyncio
    async def test_validate_token_fails_expired_token(self):
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
    async def test_validate_token_succeeds(self, init_fake_user_data, fake_user_data):
        token = await crud.login(fake_user_data[0]["name"], SecretStr(fake_user_data[0]["password"]))
        assert token is not None
        decoded_token = crud.validate_token(token)
        assert decoded_token["user_name"] == fake_user_data[0]["name"]


class TestCreateInvitation:

    @pytest.mark.asyncio
    async def test_create_invitation_fails_invitor_does_not_exist(self, init_fake_user_data, fake_user_data):
        invitee = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert invitee is not None
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            invitation = await crud.create_invitation(42069, invitee.id_)

    @pytest.mark.asyncio
    async def test_create_invitation_fails_invitee_does_not_exist(self, init_fake_user_data, fake_user_data):
        invitor = await crud.get_user_by_name(fake_user_data[0]["name"])
        with pytest.raises(sqlalchemy.exc.IntegritError):
            invitation = await crud.create_invitation(invitor.id_, 42069)

    @pytest.mark.asyncio
    async def test_create_invitation_succeeds(self, init_fake_user_data, fake_user_data):
        invitor = await crud.get_user_by_name(fake_user_data[0]["name"])
        invitee = await crud.get_user_by_name(fake_user_data[1]["name"])
        invitation = await crud.create_invitation(invitor.id_, invitee.id_)
        assert invitation is not None
        assert invitation.from_id == invitor.id_
        assert invitation.to_id == invitee.id_


@pytest.mark.asyncio
async def test_delete_invitation(init_fake_user_data):
    user_1 = await crud.get_user_by_name("fakeuser1")
    user_2 = await crud.get_user_by_name("fakeuser2")

    invitation = await crud.create_invitation(user_1.id_, user_2.id_)

    # deleteing invitation as user who recieved it is not allowed
    assert await crud.delete_invitation(invitation.id_, user_2.id_) is False

    assert await crud.delete_invitation(invitation.id_, user_1.id_) is True


@pytest.mark.asyncio
async def test_get_invitations(init_fake_user_data):
    # invitation cannot be made with non existent users

    user_1 = await crud.get_user_by_name("fakeuser1")
    user_2 = await crud.get_user_by_name("fakeuser2")

    invitation = await crud.create_invitation(user_1.id_, user_2.id_)
    result = await crud.get_invitations(id_=invitation.id_)

    assert result[0].id_ == invitation.id_
    assert result[0].from_id == invitation.from_id
    assert result[0].to_id == invitation.to_id
    assert result[0].game_type.value == invitation.game_type.value
    assert result[0].status.value == invitation.status.value


@pytest.mark.asyncio
async def test_accept_invitation(init_fake_user_data):

    # Additional things to test
    # accept/decline invitation should not be able to alter the status
    # of a non pending invitation

    # create an invitation
    user_1 = await crud.get_user_by_name("fakeuser1")
    user_2 = await crud.get_user_by_name("fakeuser2")

    invitation = await crud.create_invitation(user_1.id_, user_2.id_)

    # accept invitation
    id_ = await crud.accept_invitation(invitation.id_)

    # check if invitation.status = Accepted
    result = await crud.get_invitations(id_=invitation.id_)
    assert result[0].status.value is models.InvitationStatus.ACCEPTED.value


@pytest.mark.asyncio
async def test_decline_invitation(init_fake_user_data):
    user_1 = await crud.get_user_by_name("fakeuser1")
    user_2 = await crud.get_user_by_name("fakeuser2")

    invitation = await crud.create_invitation(user_1.id_, user_2.id_)

    id_ = await crud.decline_invitation(invitation.id_)

    result = await crud.get_invitations(id_=invitation.id_)
    assert result[0].status.value is models.InvitationStatus.DECLINED.value


@pytest.mark.asyncio
async def test_get_game(init_fake_game_data, fake_game_data):

    # assume no user has an id 666
    assert await crud.get_game(666) is None

    id_ = 1
    for data in fake_game_data:
        game = await crud.get_game(id_)
        print(game.player_1)
        print(game.invitation_id)
        id_ += 1
        assert game.player_1 == int(data["player_1"])
        assert game.player_2 == int(data["player_2"])
        assert game.whomst == int(data["whomst"])
