"""app.crud

CRUD operations

Functions:
    get_user_by_name(name: str) -> User
    get_user_by_id(id_: str) -> User
    create_user(name: str, email: str, pswd: SecretStr) -> User
    login(name: str, pswd: SecretStr) -> str
    create_invitation(from_: str, to: str, game_type: str = GameType.CHESS.value)
        -> Invitation
    get_invitation(id_: int) -> Invitation
    validate_token(token: str) -> bool
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import SecretStr
from sqlalchemy import select

from chessticulate_api.config import CONFIG
from chessticulate_api.db import async_session
from chessticulate_api.models import GameType, Invitation, User


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


async def get_user_by_name(name: str) -> User:
    """retrieve user from database by user name"""
    async with async_session() as session:
        stmt = select(User).where(User.name == name)

        row = (await session.execute(stmt)).first()
        return row if row is None else row[0]


async def get_user_by_id(id_: int) -> User:
    """retrieve user from database by user ID"""
    async with async_session() as session:
        stmt = select(User).where(User.id_ == id_)

        row = (await session.execute(stmt)).first()
        return row if row is None else row[0]


# create_user name should use pydantic SecretStr
async def create_user(name: str, email: str, pswd: SecretStr) -> User:
    """create a new user"""
    hashed_pswd = _hash_password(pswd)
    async with async_session() as session:
        user = User(name=name, email=email, password=hashed_pswd)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


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
            "user": name,
        },
        CONFIG.secret,
    )


async def create_invitation(
    from_: str, to: str, game_type: str = GameType.CHESS.value
) -> Invitation:
    """create a new invitation"""
    from_user = await get_user_by_name(from_)
    to_user = await get_user_by_name(to)
    if from_user is None:
        return None
    if to_user is None:
        return None
    async with async_session() as session:
        invitation = Invitation(
            from_=from_user.id_, to=to_user.id_, game_type=game_type
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        return invitation


async def get_invitation(id_: int) -> Invitation:
    """retrieve an invitation by ID"""
    async with async_session() as session:
        stmt = select(Invitation).where(Invitation.id_ == id_)
        row = (await session.execute(stmt)).first()
        return row if row is None else row[0]


def validate_token(token: str) -> bool:
    """validate a JWT"""
    return jwt.decode(token, CONFIG.secret, CONFIG.algorithm)
