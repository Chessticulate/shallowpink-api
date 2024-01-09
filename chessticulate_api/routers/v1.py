from fastapi import APIRouter

from chessticulate_api import crud, schemas

router = APIRouter()


@router.post("/login")
async def login(name: str, pswd: str) -> schemas.LoginResponse:
    return await crud.login(name, pswd)


@router.post("/user")
async def create_user(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:
    return dict(await crud.create_user(payload.name, payload.email, SecretStr(payload.password)))

@router.get("/user")
async def get_user(user_id: int | None = None, user_name: str | None = None) -> schemas.GetUserResponse:
    if user_id:
        return dict(await crud.get_user_by_id(user_id))
    if user_name:
        return dict(await crud.get_user_by_name(user_name))
    
