import enum
from app import db
from sqlalchemy import func, String, DateTime, ForeignKey, Enum, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class Base(DeclarativeBase):
    pass


class GameType(enum.Enum):
    CHESS = "chess"


class ResponseType(enum.Enum):
    ACCEPTED = "accepted"
    DECLINED = "declined"
    PENDING = "pending"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, server_default="FALSE")
    date_joined: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    wins: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    draws: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    losses: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_sent: Mapped[str] = mapped_column(DateTime, server_default=func.utc_timestamp())
    date_answered: Mapped[str] = mapped_column(DateTime, nullable=True)
    from_: Mapped[int] = mapped_column("from", ForeignKey("users.id"), nullable=False)
    to: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    game_type: Mapped[str] = mapped_column(Enum(GameType), nullable=False)
    response: Mapped[str] = mapped_column(Enum(ResponseType), nullable=False, server_default=ResponseType.PENDING.value)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_type: Mapped[str] = mapped_column(Enum(GameType), nullable=False)
    date_started: Mapped[str] = mapped_column(DateTime, server_default=func.utc_timestamp(), nullable=True)
    date_ended: Mapped[str] = mapped_column(DateTime, nullable=True)
    player_1: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    player_2: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    winner: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=False, server_default="{}")


Base.metadata.create_all(db.engine)

