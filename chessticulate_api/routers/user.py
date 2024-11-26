"""chessticulate_api.routers.user"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import Field

from chessticulate_api import crud, schemas, security

user_router = APIRouter(prefix="/users")


# pylint: disable=too-many-arguments, too-many-positional-arguments
@user_router.get("")
async def get_users(
    _: Annotated[dict, Depends(security.get_credentials)],
    user_id: int | None = None,
    user_name: str | None = None,
    skip: int = 0,
    limit: Annotated[int, Field(gt=0, le=50)] = 10,
    order_by: str = "date_joined",
    reverse: bool = False,
) -> schemas.GetUserListResponse:
    """Retrieve user info."""
    args = {"skip": skip, "limit": limit, "order_by": order_by, "reverse": reverse}

    if user_id:
        args["id_"] = user_id
    if user_name:
        args["name"] = user_name

    return [vars(user) for user in await crud.get_users(**args)]


@user_router.get("/name/{name}", status_code=200)
async def username_exists(name: str) -> schemas.ExistsResponse:
    """Check if a username is already taken"""
    result = await crud.get_users(name=name)
    if len(result) == 0:
        return schemas.ExistsResponse(exists=False, detail="username does not exist")
    return schemas.ExistsResponse(exists=True, detail="username exists")


@user_router.get("/email/{email}", status_code=200)
async def email_exists(email: str) -> schemas.ExistsResponse:
    """Check if an email is already taken"""
    result = await crud.get_users(email=email)
    if len(result) == 0:
        return schemas.ExistsResponse(exists=False, detail="email does not exist")
    return schemas.ExistsResponse(exists=True, detail="email exists")


@user_router.get("/self")
async def get_self(
    credentials: Annotated[dict, Depends(security.get_credentials)],
) -> schemas.GetOwnUserResponse:
    """Retrieve own user info."""
    user = await crud.get_users(id_=credentials["user_id"])
    return vars(user[0])


@user_router.delete("/self", status_code=204)
async def delete_user(credentials: Annotated[dict, Depends(security.get_credentials)]):
    """Delete own user."""
    user_id = credentials["user_id"]
    await crud.delete_user(user_id)
