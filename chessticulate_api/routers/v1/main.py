"""routers.main

fastapi endpoints

Functions:
    get_credentials(credentials: Annotated[]) -> dict
    login(payload: schemas.LoginRequest) -> schemas.LoginResponse:
    signup(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:

    get_users(credentials: Annotated[], user_id: int, user_name: str,
        skip: int = 0, limit: int = 10, order_by: str = "date_joined",
        reverse: bool = False) -> schemas.GetUserListResponse:

    delete_user(credentials: Annotated[dict, Depends(get_credentials)]):

    create_invitation(credentials: Annotated[], payload:
        schemas.CreateInvitationRequest) -> schemas.CreateInvitationResponse:

    get_invitations(credentials: Annotated[], to_id: int, from_id: int,
        invitation_id: int, status: str, skip: int = 0, limit: int = 10,
        reverse: bool = False) -> schemas.GetInvitationsListResponse:

    accept_invitation(credentials: Annotated[], invitation_id: int)
        -> schemas.AcceptInvitationResponse:

    decline_invitation(credentials: Annotated[], invitation_id: int)
    cancel_invitation(credentials: Annotated[], invitation_id: int)

"""

from typing import Annotated

import jwt
import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from chessticulate_api import crud, models
from chessticulate_api.routers.v1 import schemas

router = APIRouter()

security = HTTPBearer()


async def get_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Retrieve and validate user JWTs. For use in endpoints as dependency."""
    try:
        decoded_token = crud.validate_token(credentials.credentials)
    except jwt.exceptions.DecodeError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    except jwt.exceptions.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="expired token") from exc
    users = await crud.get_users(id_=decoded_token["user_id"])
    if not users or users[0].deleted:
        raise HTTPException(status_code=401, detail="user has been deleted")
    return decoded_token


@router.post("/login")
async def login(payload: schemas.LoginRequest) -> schemas.LoginResponse:
    """Given valid user credentials, generate JWT."""
    if not (token := await crud.login(payload.name, payload.password)):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"jwt": token}


@router.post("/signup", status_code=201)
async def signup(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:
    """Create a new user account."""
    try:
        user = await crud.create_user(payload.name, payload.email, payload.password)
    except sqlalchemy.exc.IntegrityError as ie:
        raise HTTPException(
            status_code=400, detail=f"user name '{payload.name}' already exists"
        ) from ie

    return vars(user)


# pylint: disable=too-many-arguments
@router.get("/users")
async def get_users(
    # pylint: disable=unused-argument
    credentials: Annotated[dict, Depends(get_credentials)],
    user_id: int | None = None,
    user_name: str | None = None,
    skip: int = 0,
    limit: int = 10,
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


@router.delete("/users/delete", status_code=204)
async def delete_user(credentials: Annotated[dict, Depends(get_credentials)]):
    """Delete a user. Can only by done by that user on itself."""
    user_id = credentials["user_id"]
    deleted_user = await crud.delete_user(user_id)


@router.post("/invitations", status_code=201)
async def create_invitation(
    credentials: Annotated[dict, Depends(get_credentials)],
    payload: schemas.CreateInvitationRequest,
) -> schemas.CreateInvitationResponse:
    """Send an invitation to a user."""
    if credentials["user_id"] == payload.to_id:
        raise HTTPException(status_code=400, detail="cannot invite self")

    if not (users := await crud.get_users(id_=payload.to_id)):
        raise HTTPException(status_code=400, detail="addressee does not exist")

    if users[0].deleted:
        raise HTTPException(
            status_code=400, detail=f"user '{users[0].id_}' has been deleted"
        )

    result = await crud.create_invitation(credentials["user_id"], payload.to_id)
    return vars(result)


# pylint: disable=too-many-arguments
@router.get("/invitations")
async def get_invitations(
    credentials: Annotated[dict, Depends(get_credentials)],
    to_id: int | None = None,
    from_id: int | None = None,
    invitation_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 10,
    reverse: bool = False,
) -> schemas.GetInvitationsListResponse:
    """Retrieve a list of invitations."""
    if not (to_id or from_id):
        raise HTTPException(
            status_code=400, detail="'to_id' or 'from_id' must be supplied"
        )
    if from_id != credentials["user_id"] and to_id != credentials["user_id"]:
        raise HTTPException(
            status_code=400,
            detail="'to_id' or 'from_id' must match the requestor's user ID",
        )

    args = {"skip": skip, "limit": limit, "reverse": reverse}

    if to_id:
        args["to_id"] = to_id
    if from_id:
        args["from_id"] = from_id
    if invitation_id:
        args["id_"] = invitation_id
    if status:
        args["status"] = status
    result = await crud.get_invitations(**args)

    return [vars(inv) for inv in result]


@router.put("/invitations/{invitation_id}/accept")
async def accept_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int
) -> schemas.AcceptInvitationResponse:
    """Accept an invitation and start a game."""

    invitation_list = await crud.get_invitations(id_=invitation_id)

    if not invitation_list:
        raise HTTPException(
            status_code=404,
            detail=f"invitation with ID '{invitation_id}' does not exist",
        )

    invitation = invitation_list[0]
    if credentials["user_id"] != invitation.to_id:
        raise HTTPException(
            status_code=403,
            detail=(
                f"invitation with ID '{invitation_id}' not addressed to user with ID"
                f" '{credentials['user_id']}'"
            ),
        )

    user = await crud.get_users(id_=invitation.from_id)
    if user[0].deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"user with ID '{invitation.from_id}' who sent invitation with id"
                f" '{invitation_id}' does not exist"
            ),
        )

    if invitation.status != models.InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=(
                f"invitation with ID '{invitation_id}' already has"
                f" '{invitation.status.value}' status"
            ),
        )

    if not (result := await crud.accept_invitation(invitation_id)):
        # possible race condition
        raise HTTPException(status_code=500)

    return {"game_id": result.id_}


@router.put("/invitations/{invitation_id}/decline")
async def decline_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int
):
    """Decline an invitation."""
    invitation_list = await crud.get_invitations(id_=invitation_id)

    if not invitation_list:
        raise HTTPException(
            status_code=404,
            detail=f"invitation with ID '{invitation_id}' does not exist",
        )

    invitation = invitation_list[0]
    if credentials["user_id"] != invitation.to_id:
        raise HTTPException(
            status_code=403,
            detail=(
                f"invitation with ID '{invitation_id}' not addressed to user with ID"
                f" '{credentials['user_id']}'"
            ),
        )

    user = await crud.get_users(id_=invitation.from_id)
    if user[0].deleted:
        raise HTTPException(
            status_code=404,
            detail=(
                f"user with ID '{invitation.from_id}' who sent invitation with id"
                f" '{invitation_id}' does not exist"
            ),
        )

    if invitation.status != models.InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=(
                f"invitation with ID '{invitation_id}' already has"
                f" '{invitation.status.value}' status"
            ),
        )

    if not await crud.decline_invitation(invitation_id):
        raise HTTPException(status_code=500)


@router.put("/invitations/{invitation_id}/cancel")
async def cancel_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int
):
    """Cancel an invitation."""

    invitation_list = await crud.get_invitations(id_=invitation_id)

    if not invitation_list:
        raise HTTPException(
            status_code=404,
            detail=f"invitation with ID '{invitation_id}' does not exist",
        )

    invitation = invitation_list[0]
    if credentials["user_id"] != invitation.from_id:
        raise HTTPException(
            status_code=403,
            detail=(
                f"invitation with ID '{invitation_id}' not sent by user with ID"
                f" '{credentials['user_id']}'"
            ),
        )

    if invitation.status != models.InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=(
                f"invitation with ID '{invitation_id}' already has"
                f" '{invitation.status.value}' status"
            ),
        )

    if not await crud.cancel_invitation(invitation_id):
        raise HTTPException(status_code=500)
