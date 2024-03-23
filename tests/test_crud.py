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
    async def test_get_user_by_name_does_not_exist(self):
        user = await crud.get_user_by_name("nonexistentuser")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_name_succeeds(self, fake_user_data):
        user = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert user is not None
        assert user.name == fake_user_data[0]["name"]


class TestGetUserById:

    @pytest.mark.asyncio
    async def test_get_user_by_id_does_not_exist(self):
        user = await crud.get_user_by_id("4")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_succeeds(self):
        user = await crud.get_user_by_id("1")
        assert user is not None


class TestCreateUser:

    @pytest.mark.asyncio
    async def test_create_user_fails_duplicate_name(self, fake_user_data):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await crud.create_user(fake_user_data[0]["name"], "unique@fakeemail.com", SecretStr(fake_user_data[0]["password"]))

    @pytest.mark.asyncio
    async def test_create_user_fails_duplicate_email(self, fake_user_data):
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            await crud.create_user("unique", fake_user_data[0]["email"], SecretStr(fake_user_data[0]["password"]))

    @pytest.mark.asyncio
    async def test_create_user_succeeds(self, restore_fake_data_after):
        user = await crud.create_user("unique", "unique@fakeemail.com", SecretStr("password"))
        assert user is not None
        assert user.name == "unique"
        assert user.email == "unique@fakeemail.com"


class TestDeleteUser:

    @pytest.mark.asyncio
    async def test_delete_user_fails_does_not_exist(self):
        assert await crud.delete_user(42069) == False

    @pytest.mark.asyncio
    async def test_delete_user_succeeds_and_cant_be_deleted_again(self, restore_fake_data_after, fake_user_data):
        user = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert user is not None
        assert await crud.delete_user(user.id_) is True
        assert await crud.get_user_by_name(user.name) is None
        assert await crud.delete_user(user.id_) is False


class TestLogin:

    @pytest.mark.asyncio
    async def test_login_fails_user_does_not_exist(self):
        token = await crud.login("doesnotexist", SecretStr("password"))
        assert token is None

    @pytest.mark.asyncio
    async def test_login_fails_bad_password(self, fake_user_data):
        token = await crud.login(fake_user_data[0]["name"], SecretStr("wrongpassword"))
        assert token is None

    @pytest.mark.asyncio
    async def test_login_fails_user_deleted(self, fake_user_data):
        user = await crud.get_user_by_name(fake_user_data[0]["name"])
        assert user is not None
        assert await crud.delete_user(user.id_) is True
        token = await crud.login(fake_user_data[0]["name"], fake_user_data[0]["password"])
        assert token is None

    @pytest.mark.asyncio
    async def test_login_succeeds(self, fake_user_data):
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
    async def test_validate_token_succeeds(self, fake_user_data):
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
    async def test_create_invitation_succeeds(self, restore_fake_data_after, fake_user_data):
        invitor = await crud.get_user_by_name(fake_user_data[0]["name"])
        invitee = await crud.get_user_by_name(fake_user_data[1]["name"])
        invitation = await crud.create_invitation(invitor.id_, invitee.id_)
        assert invitation is not None
        assert invitation.from_id == invitor.id_
        assert invitation.to_id == invitee.id_
        assert invitation.status == models.InvitationStatus.PENDING
        assert invitation.game_type == models.GameType.CHESS


class TestGetInvitations:

    @pytest.mark.parametrize(
        "query_params", [
            {"id_": 42069},
            {"to_id": 42069},
            {"from_id": 2, "to_id": 1},
            {"from_id": 3, "to_id": 1, "status": models.InvitationStatus.PENDING},
        ]
    )
    @pytest.mark.asyncio
    async def test_get_invitations_fails_doesnt_exist(self, query_params):
        invitations = await crud.get_invitations(**query_params)
        assert invitations == [], f"id_={invitations[0].id_}, status={invitations[0].status}, deleted={invitations[0].deleted}"

    @pytest.mark.asyncio
    async def test_get_invitations_fails_is_deleted(self, fake_invitation_data):
        deleted_invite = fake_invitation_data[4]
        invitations = await crud.get_invitations(from_id=deleted_invite["from_id"], to_id=deleted_invite["to_id"], status=deleted_invite["status"])
        assert invitations == [], f"id_={invitations[0].id_}, status={invitations[0].status}, deleted={invitations[0].deleted}"

    @pytest.mark.parametrize(
        "query_params,expected_count",
        [
            ({"status": models.InvitationStatus.ACCEPTED}, 3),
            ({"status": models.InvitationStatus.PENDING}, 1),
            ({"from_id": 1}, 2),
            ({"to_id": 3}, 1),
        ]
    )
    @pytest.mark.asyncio
    async def test_get_invitations_succeeds(self, query_params, expected_count):
        invitations = await crud.get_invitations(**query_params)
        assert len(invitations) == expected_count


class TestCancelInvitation:

    @pytest.mark.asyncio
    async def test_cancel_invitation_fails_doesnt_exist(self):
        assert await crud.cancel_invitation(42069) is False

    @pytest.mark.asyncio
    async def test_cancel_invitation_fails_not_pending(self):
        assert await crud.cancel_invitation(1) is False

    @pytest.mark.asyncio
    async def test_cancel_invitation_succeeds(self, restore_fake_data_after):
        invitation = await crud.get_invitations(id_=3)

        assert invitation.status == models.InvitationStatus.PENDING
        assert await crud.cancel_invation(3) is True

        invitation = await crud.get_invitations(id_=3)

        assert invitation.status == models.InvitationStatus.CANCELLED


class TestDeclineInvitation:

    @pytest.mark.asyncio
    async def test_decline_invitation_fails_doesnt_exist(self):
        assert await crud.decline_invitation(42069) is False

    @pytest.mark.asyncio
    async def test_decline_invitation_fails_not_pending(self):
        assert await crud.decline_invitation(6) is False

    @pytest.mark.asyncio
    async def test_decline_invitation_succeeds(self, restore_fake_data_after):
        invitation = await crud.get_invitations(id_=3)

        assert invitation.status == models.InvitationStatus.PENDING
        assert await crud.decline_invitation(4) is True

        invitation = await crud.get_invitations(id_=3)

        assert invitation.status == models.InvitationStatus.DECLINED


class TestAcceptInvitation:

    @pytest.mark.asyncio
    async def test_accept_invitation_fails_doesnt_exist(self):
        assert await crud.accept_invitation(42069) is None

    @pytest.mark.asyncio
    async def test_accept_invitation_fails_not_pending(self):
        assert await crud.accept_invitation(1) is None

    @pytest.mark.asyncio
    async def test_accept_invitation_succeeds(self, restore_fake_data_after):
        invitation = await crud.get_invitations(id_=4)

        assert invitation.status == models.InvitationStatus.PENDING

        game = await crud.accept_invitation(4)
        invitation = await crud.get_invitations(id_=4)

        assert game is not None
        assert game.invitation_id == invitation.id_
        assert game.player_1 == invitation.from_id
        assert game.player_2 == invitation.to_id
        assert invitation.status == models.InvitationStatus.ACCEPTED


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
