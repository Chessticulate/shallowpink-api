"""app.crud

CRUD operations

Functions:
    get_user_by_name(name: str) -> models.User
    get_user_by_id(id_: str) -> models.User
    create_user(name: str, email: str, pswd: SecretStr) -> models.User
    login(name: str, pswd: SecretStr) -> str
    create_invitation(from_: str, to: str, game_type: str = models.GameType.CHESS.value)
        -> models.Invitation
    get_invitations(*, skip: int = 0, limit: int = 10, reverse: bool = False, **kwargs) -> list[models.Invitation]:
    validate_token(token: str) -> bool
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import SecretStr
from sqlalchemy import select

from chessticulate_api import models
from chessticulate_api.config import CONFIG
from chessticulate_api.db import async_session


def _hash_password(pswd: SecretStr) -> str:
    """hash password using bcrypt"""
    return bcrypt.hashpw(  # pylint: disable=no-member
        pswd.get_secret_value(), bcrypt.gensalt()
    )


def _check_password(pswd: SecretStr, pswd_hash: str) -> bool:
    """compare password with password hash using bcrypt"""
    return bcrypt.checkpw(  # pylint: disable=no-member
        pswd.get_secret_value(), pswd_hash
    )


def validate_token(token: str) -> dict:
    """validate a JWT"""
    return jwt.decode(token, CONFIG.secret, CONFIG.algorithm)


async def get_user_by_name(name: str) -> models.User:
    """retrieve user from database by user name"""
    async with async_session() as session:
        stmt = select(models.User).where(models.User.name == name)

        row = (await session.execute(stmt)).first()
        return row if row is None else row[0]


async def get_user_by_id(id_: int) -> models.User:
    """retrieve user from database by user ID"""
    async with async_session() as session:
        stmt = select(models.User).where(models.User.id_ == id_)

        row = (await session.execute(stmt)).first()
        return row if row is None else row[0]


# create_user name should use pydantic SecretStr
async def create_user(name: str, email: str, pswd: SecretStr) -> models.User:
    """create a new user"""
    hashed_pswd = _hash_password(pswd)
    async with async_session() as session:
        user = models.User(name=name, email=email, password=hashed_pswd)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


# WIP need to check if user is logged in so that they have permission to delete account
async def delete_user(id_: int):
    """delete existing user"""
    async with async_session() as session:
        
        stmt = (
            update(models.User)
            .where(models.User.id_ == id_)
            .values(password=None, email=None, deleted=True)
        )
        await session.execute(stmt)
        await session.commit()


async def login(name: str, pswd: SecretStr) -> str:
    """validate user name and password, return a JWT"""
    user = await get_user_by_name(name)
    if user is None:
        return None
    if not _check_password(pswd, user.password):
        return None
    return jwt.encode(
        {
            "exp": datetime.now(tz=timezone.utc) + timedelta(days=CONFIG.token_ttl),
            "user_name": name,
            "user_id": user.id_,
        },
        CONFIG.secret,
    )


async def create_invitation(
    from_id: int, to_id: int, game_type: models.GameType = models.GameType.CHESS
) -> models.Invitation:
    """create a new invitation"""
    async with async_session() as session:
        invitation = models.Invitation(
            from_id=from_id, to_id=to_id, game_type=game_type
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        return invitation


# invitation deletable only by user who sent it
async def delete_invitation(id_: int, from_id: int) -> models.Invitation:
    invitation = await get_invitations(id_)
    if invitation is None:
        return None

    if invitation.from_id != from_id:
        return None

    async with async_session() as session:
        await session.delete(invitation)
        await session.commit()
        return invitation


async def get_invitations(
    *, skip: int = 0, limit: int = 10, reverse: bool = False, **kwargs
) -> list[models.Invitation]:
    """retrieve invitations from DB

    Examples:
        # get invitation by ID
        get_invitations(id_=10)

        # get pending invitations addressed to user with ID 3
        get_invitations(skip=0, limit=5, to=3, status='PENDING')

        # TODO: add 'since' and 'before' parameters
    """
    async with async_session() as session:
        stmt = select(models.Invitation)
        for k, v in kwargs.items():
            stmt = stmt.where(getattr(models.Invitation, k) == v)

        if reverse:
            stmt = stmt.order_by(models.Invitation.date_sent.desc())
        else:
            stmt = stmt.order_by(models.Invitation.date_sent.asc())

        stmt = stmt.offset(skip).limit(limit)
        return [row[0] for row in (await session.execute(stmt)).all()]


async def accept_invitation(id_: int) -> models.Game:
    """respond to pending invitation"""
    async with async_session() as session:
        invitation = session.get(models.Invitation, id_)
        invitation.status = models.InvitationStatus.ACCEPTED

        new_game = models.Game(
            player1=invitation.from_id,
            player2=invitation.to_id,
            whomst=invitation.from_id,
            invitation_id=id_,
        )
        session.add(new_game)
        await session.commit()
        return new_game.id_


async def decline_invitation(id_: int):
    """decline pending invitation"""
    async with async_session() as session:
        stmt = (
            update(models.Invitation)
            .where(models.Invitation.id_ == id_)
            .values(status=models.InvitationStatus.DECLINED)
        )
        await session.execute(stmt)
        await session.commit()
