import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from chessticulate_api import crud, schemas

router = APIRouter()

security = HTTPBearer()


def get_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    try:
        decoded_token = crud.validate_token(credentials.credentials)
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=401, detail="invalid token")
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="expired token")
    return decoded_token


@router.post("/login")
async def login(name: str, pswd: str) -> schemas.LoginResponse:
    return await crud.login(name, pswd)


@router.post("/signup")
async def signup(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:
    return dict(
        await crud.create_user(payload.name, payload.email, SecretStr(payload.password))
    )


@router.get("/user")
async def get_user(
    credentials: Annotated[dict, Depends(get_credentials)],
    user_id: int | None = None,
    user_name: str | None = None,
) -> schemas.GetUserResponse:
    if user_id:
        return dict(await crud.get_user_by_id(user_id))
    if user_name:
        return dict(await crud.get_user_by_name(user_name))

    raise HTTPException(
        status_code=400, detail="must provide either 'user_id' or 'user_name'"
    )


@router.post("/invitation")
async def create_invitation(
    credentials: Annotated[dict, Depends(get_credentials)],
    payload: schemas.CreateInviteRequest,
) -> schemas.CreateInviteResponse:
    return dict(await crud.create_invitation(credentials["user_id"], payload.to))
