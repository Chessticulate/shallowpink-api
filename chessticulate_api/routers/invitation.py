"""chessticulate_api.routers.invitation"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from chessticulate_api import crud, models, schemas, security

invitation_router = APIRouter(prefix="/invitations")


@invitation_router.post("", status_code=201)
async def create_invitation(
    credentials: Annotated[dict, Depends(security.get_credentials)],
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
@invitation_router.get("")
async def get_invitations(
    credentials: Annotated[dict, Depends(security.get_credentials)],
    to_id: int | None = None,
    from_id: int | None = None,
    invitation_id: int | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: Annotated[int, Field(strict=True, gt=0, le=50)] = 10,
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


@invitation_router.put("/{invitation_id}/accept")
async def accept_invitation(
    credentials: Annotated[dict, Depends(security.get_credentials)], invitation_id: int
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


@invitation_router.put("/{invitation_id}/decline")
async def decline_invitation(
    credentials: Annotated[dict, Depends(security.get_credentials)], invitation_id: int
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


@invitation_router.put("/{invitation_id}/cancel")
async def cancel_invitation(
    credentials: Annotated[dict, Depends(security.get_credentials)], invitation_id: int
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
