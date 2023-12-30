from app.models import db, User, Invitation, GameType
from app.config import CONFIG
from sqlalchemy.orm import Session
from sqlalchemy import select, insert
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from pydantic import SecretStr, constr


def hash_password(pswd: SecretStr) -> str:
    return bcrypt.hashpw(pswd.get_secret_value(), bcrypt.gensalt())


def check_password(pswd: SecretStr, pswd_hash: str) -> bool:
    return bcrypt.checkpw(pswd.get_secret_value(), pswd_hash)


def get_user_by_name(name: str) -> User:
    with Session(db.engine) as session:
        stmt = select(User).where(User.name == name)

        row = session.execute(stmt).first()
        return row if row is None else row[0]


def get_user_by_id(id: int) -> User:
    with Session(db.engine) as session:
        stmt = select(User).where(User.id == id)

        row = session.execute(stmt).first()
        return row if row is None else row[0]


# create_user name should use pydantic SecretStr
def create_user(name: str, email: str, pswd: SecretStr) -> User:
    hashed_pswd = hash_password(pswd)
    with Session(db.engine) as session:
        user = User(name=name, email=email, password=hashed_pswd)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def login(name: str, pswd: SecretStr) -> str:
    user = get_user_by_name(name)
    if user is None:
        return None
    if not check_password(pswd, user.password):
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
    from_user = get_user_by_name(from_)
    to_user = get_user_by_name(to)
    if from_user is None:
        return None
    if to_user is None:
        return None
    with Session(db.engine) as session:
        invitation = Invitation(from_=from_user.id, to=to_user.id, game_type=game_type)
        session.add(invitation)
        session.commit()
        session.refresh(invitation)
        return invitation


def get_invite(id: int) -> Invitation:
    with Session(db.engine) as session:
        stmt = select(Invitation).where(Invitation.id == id)
        row = session.execute(stmt).first()
        return row if row is None else row[0]


def validate_token(token: str) -> bool:
    return jwt.decode(token, CONFIG.secret, CONFIG.algorithm)
