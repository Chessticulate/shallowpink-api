"""app.schemas

Pydantic schemas for FastAPI endpoints.

Classes:
    CreateInvite
    LoginResponse
    CreateUserResponse
    CreateUserRequest
"""

from pydantic import BaseModel, EmailStr, SecretStr, StringConstraints
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated


class CreateInviteRequest(BaseModel):
    """Pydantic model for invite creation requests."""

    to: str
    game_type: str

class CreateInviteResponse(BaseModel):
    """pydantic model for invite creation response"""
    
    id_: int
    date_sent: str
    date_answered: str
    from_: int
    to: int
    game_type: str
    response: str
    
class LoginResponse(BaseModel):
    """Pydantic model for login responses."""

    jwt: str


class CreateUserResponse(BaseModel):
    """Pydantic model for user creation responses."""

    id: int
    name: str
    email: str
    date_joined: str
    wins: int
    draws: int
    losses: int


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

class GetUserResponse(CreateUserResponse):
    """Pydantic model for get user response"""


