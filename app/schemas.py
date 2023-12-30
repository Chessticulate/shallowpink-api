from pydantic import BaseModel, constr, EmailStr


class CreateInvite(BaseModel):
    to: str
    game_type: str


class LoginResponse(BaseModel):
    jwt: str


class CreateUserResponse(BaseModel):
    id: int
    name: str
    email: str
    deleted: bool
    date_joined: str
    wins: int
    draws: int
    losses: int


class CreateUserRequest(BaseModel):
    name: constr(min_length=3, max_length=15, regex=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: constr(min_length=8, max_length=20)
