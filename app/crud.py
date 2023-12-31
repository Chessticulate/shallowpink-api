"""app.crud

CRUD operations

Functions:
    get_user_by_name(name: str) -> User
    get_user_by_id(id_: str) -> User
    create_user(name: str, email: str, pswd: SecretStr) -> User
    login(name: str, pswd: SecretStr) -> str
    create_invite(from_: str, to: str, game_type: str = GameType.CHESS.value) -> Invitation
    get_invite(id_: int) -> Invitation
    validate_token(token: str) -> bool
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import CONFIG
from app.models import GameType, Invitation, User, db


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


def get_user_by_name(name: str) -> User:
    """retrieve user from database by user name"""
    with Session(db.engine) as session:
        stmt = select(User).where(User.name == name)

        row = session.execute(stmt).first()
        return row if row is None else row[0]


def get_user_by_id(id_: int) -> User:
    """retrieve user from database by user ID"""
    with Session(db.engine) as session:
        stmt = select(User).where(User.id_ == id_)

        row = session.execute(stmt).first()
        return row if row is None else row[0]


# create_user name should use pydantic SecretStr
def create_user(name: str, email: str, pswd: SecretStr) -> User:
    """create a new user"""
    hashed_pswd = _hash_password(pswd)
    with Session(db.engine) as session:
        user = User(name=name, email=email, password=hashed_pswd)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def login(name: str, pswd: SecretStr) -> str:
    """validate user name and password, return a JWT"""
    user = get_user_by_name(name)
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


def create_invite(
    from_: str, to: str, game_type: str = GameType.CHESS.value
) -> Invitation:
    """create a new invitation"""
    from_user = get_user_by_name(from_)
    to_user = get_user_by_name(to)
    if from_user is None:
        return None
    if to_user is None:
        return None
    with Session(db.engine) as session:
        invitation = Invitation(
            from_=from_user.id_, to=to_user.id_, game_type=game_type
        )
        session.add(invitation)
        session.commit()
        session.refresh(invitation)
        return invitation


def get_invite(id_: int) -> Invitation:
    """retrieve an invitation by ID"""
    with Session(db.engine) as session:
        stmt = select(Invitation).where(Invitation.id_ == id_)
        row = session.execute(stmt).first()
        return row if row is None else row[0]


def validate_token(token: str) -> bool:
    """validate a JWT"""
    return jwt.decode(token, CONFIG.secret, CONFIG.algorithm)
