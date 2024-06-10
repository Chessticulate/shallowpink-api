"""chessticulate_api.routers.user"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import Field

from chessticulate_api import crud, schemas, security

user_router = APIRouter(prefix="/users")


# pylint: disable=too-many-arguments
@user_router.get("")
async def get_users(
    # pylint: disable=unused-argument
    credentials: Annotated[dict, Depends(security.get_credentials)],
    user_id: int | None = None,
    user_name: str | None = None,
    skip: int = 0,
    limit: Annotated[int, Field(gt=0, le=50)] = 10,
    order_by: str = "date_joined",
    reverse: bool = False,
) -> schemas.GetUserListResponse:
    """Retrieve user info."""
    if user_id:
        return [vars(user) for user in await crud.get_users(id_=user_id)]

    if user_name:
        return [vars(user) for user in await crud.get_users(name=user_name)]

    args = {"skip": skip, "limit": limit, "order_by": order_by, "reverse": reverse}

    return [vars(user) for user in await crud.get_users(**args)]


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
