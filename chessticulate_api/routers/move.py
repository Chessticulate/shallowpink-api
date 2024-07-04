"""chessticulate_api.routers.move"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import Field

from chessticulate_api import crud, schemas, security

move_router = APIRouter(prefix="/moves")


# pylint: disable=too-many-arguments
@move_router.get("")
async def get_moves(
    # pylint: disable=unused-argument
    credentials: Annotated[dict, Depends(security.get_credentials)],
    move_id: int | None = None,
    user_id: int | None = None,
    game_id: int | None = None,
    skip: int = 0,
    limit: Annotated[int, Field(gt=0, le=50)] = 10,
    reverse: bool = False,
) -> schemas.GetMovesListResponse:
    """Retrieve a list of Moves"""
    if move_id:
        return [vars(move) for move in await crud.get_moves(id_=move_id)]

    args = {"skip": skip, "limit": limit, "reverse": reverse}
    if user_id:
        args["user_id"] = user_id
    if game_id:
        args["game_id"] = game_id

    moves = await crud.get_moves(**args)

    return [vars(move) for move in moves]
