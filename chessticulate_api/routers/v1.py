from fastapi import APIRouter, HTTPException
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

    raise HTTPException(status_code=400, detail="must provide either 'user_id' or 'user_name'") 

@router.post("/invitation")
async def create_invitation(payload: schemas.CreateInviteRequest) -> schemas.CreateInviteResponse:
    return dict(await crud.create_invitation(payload.from_, payload.to))
