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
from typing import Union

from pydantic import BaseModel, EmailStr, Field, RootModel, SecretStr, StringConstraints
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


class GameTypeEnum(str, enum.Enum):
    """Game Type Enum"""

    CHESS = "CHESS"


class CreateInvitationRequest(BaseModel):
    """Pydantic model for invite creation requests."""

    to_id: int
    game_type: GameTypeEnum = GameTypeEnum.CHESS

    class Config:  # pylint: disable=missing-class-docstring,too-few-public-methods
        use_enum_values = True


class CreateInvitationResponse(BaseModel):
    """pydantic model for invite creation response"""

    id_: int = Field(..., alias="id_")
    date_sent: datetime
    date_answered: None
    from_id: int
    to_id: int
    game_type: str
    status: str


class DeleteInvitationResponse(BaseModel):
    """pydantic model for delete invite response"""

    id_: int = Field(..., alias="id")
    date_sent: str
    date_answered: str
    from_id: int
    to_id: int
    game_type: str
    response: str


class GetInvitationResponse(BaseModel):
    """pydantic model for get invitation response"""

    id_: int = Field(..., alias="id_")
    date_sent: datetime
    date_answered: Union[datetime, None]
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


class CreateUserResponse(BaseModel):
    """Pydantic model for user creation responses."""

    name: str
    email: str
    password: str


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

    id_: int = Field(..., alias="id_")
    name: str
    email: str
    date_joined: datetime
    wins: int
    draws: int
    losses: int


class GetUserListResponse(RootModel):
    """Pydantic model for returning a list of GetUserResponses"""

    root: list[GetUserResponse]


class GetInvitationsListResponse(RootModel):
    """Pydantic model for returning a list of GetInvitationResponses"""

    root: list[GetInvitationResponse]


class AcceptInvitationResponse(BaseModel):
    """Pydantic model for accepting game invitation"""

    game_id: int
