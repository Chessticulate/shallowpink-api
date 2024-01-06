from fastapi import APIRouter

from chessticulate_api import crud, schemas

router = APIRouter()


@router.post("/login")
def login(name: str, pswd: str) -> schemas.LoginResponse:
    return crud.login(name, pswd)


@router.post("/create_user")
def create_user(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:
    return crud.create_user(payload.name, payload.email, SecretStr(payload.password))
