"""app.schemas

Pydantic schemas for FastAPI endpoints.

Classes:
    CreateInvitation
    LoginResponse
    CreateUserResponse
    CreateUserRequest
"""

import enum
from datetime import datetime

from pydantic import (
    AliasChoices,
    BaseModel,
    EmailStr,
    Field,
    RootModel,
    SecretStr,
    StringConstraints,
)
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


class GameTypeEnum(str, enum.Enum):
    """Game Type Enum"""

    CHESS = "CHESS"


class CreateInvitationRequest(BaseModel):
    """Pydantic model for invite creation requests."""

    to_id: int
    game_type: GameTypeEnum = GameTypeEnum.CHESS

    model_config = {"use_enum_values": True}


class CreateInvitationResponse(BaseModel):
    """pydantic model for invite creation response"""

    id_: int = Field(
        ..., validation_alias=AliasChoices("id_", "id"), serialization_alias="id"
    )
    date_sent: datetime
    date_answered: datetime | None
    from_id: int
    to_id: int
    game_type: str
    status: str


class GetInvitationResponse(BaseModel):
    """pydantic model for get invitation response"""

    id_: int = Field(
        ..., validation_alias=AliasChoices("id_", "id"), serialization_alias="id"
    )
    date_sent: datetime
    date_answered: datetime | None
    from_id: int
    to_id: int
    game_type: str
    status: str


class LoginRequest(BaseModel):
    """pydantic Model fro Login Requests"""

    name: str
    password: SecretStr


class LoginResponse(BaseModel):
    """Pydantic model for login responses."""

    jwt: str


def _validate_password(s: str) -> str:
    """Make sure new password conforms to rules"""
    assert len(s) >= 8, "Password is too short (<8 characters)"
    assert len(s) <= 64, "Password is too long (>64 characters)"
    has_lower, has_upper, has_number, has_special = False, False, False, False
    for c in s:
        if c.islower():
            has_lower = True
        if c.isupper():
            has_upper = True
        if c.isdigit():
            has_number = True
        if not c.isalnum():
            has_special = True
    assert has_lower and has_upper and has_number and has_special, (
        "Password is missing requirements (at least 1 upper, 1 lower, 1 number and 1"
        " special character)"
    )
    return s


class CreateUserRequest(BaseModel):
    """Pydantic model for user creation requests."""

    name: Annotated[
        str, StringConstraints(min_length=3, max_length=15, pattern=r"^[a-zA-Z0-9_-]+$")
    ]
    email: EmailStr
    password: Annotated[SecretStr, BeforeValidator(_validate_password)]


class GetUserResponse(BaseModel):
    """Pydantic model for get user response."""

    id_: int = Field(
        ..., validation_alias=AliasChoices("id_", "id"), serialization_alias="id"
    )
    name: str
    date_joined: datetime
    wins: int
    draws: int
    losses: int


class GetOwnUserResponse(GetUserResponse):
    """Pydantic model for getting own user info"""

    email: str


class GetUserListResponse(RootModel):
    """Pydantic model for returning a list of GetUserResponses"""

    root: list[GetUserResponse]


class GetInvitationsListResponse(RootModel):
    """Pydantic model for returning a list of GetInvitationResponses"""

    root: list[GetInvitationResponse]


class AcceptInvitationResponse(BaseModel):
    """Pydantic model for accepting game invitation"""

    game_id: int


class GetGameResponse(BaseModel):
    """Pydantic model for get game response"""

    id_: int = Field(
        ..., validation_alias=AliasChoices("id_", "id"), serialization_alias="id"
    )
    game_type: str
    date_started: datetime
    invitation_id: int
    date_ended: datetime | None = None
    player_1: int
    player_2: int
    whomst: int
    winner: int | None = None
    fen: str


class GetGamesListResponse(RootModel):
    """Pydantic model for returning a list of GetGameResponses"""

    root: list[GetGameResponse]


class DoMoveRequest(BaseModel):
    """Pydantic model for move endpoint request"""

    move: str


class GetMovesResponse(BaseModel):
    """Pydantic model for get move responses"""

    id_: int = Field(
        ..., validation_alias=AliasChoices("id_", "id"), serialization_alias="id"
    )
    user_id: int
    game_id: int
    timestamp: datetime | None = None
    movestr: str
    fen: str


class GetMovesListResponse(RootModel):
    """Pydantic model for returning a list of GetMovesResponses"""

    root: list[GetMovesResponse]
