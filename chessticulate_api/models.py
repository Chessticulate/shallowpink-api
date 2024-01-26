"""app.models

SQLAlchemy ORM models

Classes:
    Base
    GameType
    User
    Invitation
    InvitationStatus
    Game

Functions:
    init_db
"""

import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from chessticulate_api.db import async_engine


class Base(DeclarativeBase):  # pylint: disable=too-few-public-methods
    """Base SQLAlchemy ORM Class"""


class GameType(enum.Enum):
    """GameType Enum

    This enum contains the available game types.
    """

    CHESS = "CHESS"


class InvitationStatus(enum.Enum):
    """Invitation Response Enum"""

    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    PENDING = "PENDING"


class User(Base):  # pylint: disable=too-few-public-methods
    """User SQL Model"""

    __tablename__ = "users"

    id_: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, server_default="FALSE")
    date_joined: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.now(),  # pylint: disable=not-callable
        nullable=False,
    )
    wins: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    draws: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    losses: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class Invitation(Base):  # pylint: disable=too-few-public-methods
    """Invitation SQL Model"""

    __tablename__ = "invitations"

    id_: Mapped[int] = mapped_column(primary_key=True)
    date_sent: Mapped[str] = mapped_column(
        DateTime, server_default=func.now()  # pylint: disable=not-callable
    )
    date_answered: Mapped[str] = mapped_column(DateTime, nullable=True)
    from_: Mapped[int] = mapped_column("from", ForeignKey("users.id_"), nullable=False)
    to: Mapped[int] = mapped_column(ForeignKey("users.id_"), nullable=False)
    game_type: Mapped[str] = mapped_column(Enum(GameType), nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(InvitationStatus), nullable=False, server_default=InvitationStatus.PENDING.value
    )


class Game(Base):  # pylint: disable=too-few-public-methods
    """Game SQL Model"""

    __tablename__ = "games"

    id_: Mapped[int] = mapped_column(primary_key=True)
    game_type: Mapped[str] = mapped_column(Enum(GameType), nullable=False)
    date_started: Mapped[str] = mapped_column(
        DateTime, server_default=func.utc_timestamp(), nullable=True
    )
    date_ended: Mapped[str] = mapped_column(DateTime, nullable=True)
    player_1: Mapped[int] = mapped_column(ForeignKey("users.id_"), nullable=True)
    player_2: Mapped[int] = mapped_column(ForeignKey("users.id_"), nullable=True)
    winner: Mapped[int] = mapped_column(ForeignKey("users.id_"), nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, server_default="{}")


async def init_db():
    """Submit DDL to database"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
