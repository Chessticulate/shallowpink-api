from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from chessticulate_api import crud
from chessticulate_api.routers.v1 import schemas

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
    if user_name: return dict(await crud.get_user_by_name(user_name))

    raise HTTPException(
        status_code=400, detail="must provide either 'user_id' or 'user_name'"
    )


@router.post("/invitation")
async def create_invitation(
    credentials: Annotated[dict, Depends(get_credentials)],
    payload: schemas.CreateInvitationRequest,
) -> schemas.CreateInvitationResponse:
    return dict(await crud.create_invitation(credentials["user_id"], payload.to))


@router.get("/invitations")
async def get_invitations(
        credentials: Annotated[dict, Depends(get_credentials)], 
        to_id: int | None = None,
        from_id: int | None = None,
        invitation_id: int | None = None,
        status: str | None = None,
        skip: int | None = 10,
        limit: int | None = 1) -> schemas.GetInvitationResponse:
    if not (to_id or from_id):
        raise HTTPException(status_code=400, detail="'to_id' or 'from_id' must be supplied")
    if from_id != credentials["user_id"] and to_id != credentials["user_id"]
        raise HTTPException(status_code=400, detail="'to_id' or 'from_id' must match the requestor's user ID")           

    args = {
        "skip": skip,
        "limit": limit
    }
    if to_id:
        args["to_id"] = to_id
    if from_id:
        args["from_id"] = from_id
    if invitation_id: 
        args["invitation_id"] = invitation_id
    if status:
        args["status"] = status
    result = await crud.get_invitations(**args)
   
    return [dict(inv) for inv in result]



@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int) -> schemas.AcceptInvitationResponse:
    # check if user who SENT invitation still exists

    invitation_list = get_invitations(id_ = invitation_id)
    
    if not invitation_list:
        raise HTTPException(status_code=404, detail=f"invitation with ID '{invitation_id}' does not exist")
    invitation = invitation_list[0]
    if credentials["user_id"] != invitation.to_id:
        raise HTTPException(status_code=403, detail=f"invitation with ID '{invitation_id}' not addressed to user with ID '{credentials[\"user_id\"]'")

    if invitation.status != model.InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"invitation with ID '{invitation_id}' already has '{invitation.status.value}' status")
    
    result = await crud.accept_invitation(invitation_id) 

    return result.id_

@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int):
    
    invitation_list = get_invitations(id_ = invitation_id)
 
    if not invitation_list:
        raise HTTPException(status_code=404, detail=f"invitation with ID '{invitation_id}' does not exist")

    invitation = invitation_list[0]
    if credentials["user_id"] != invitation.to_id: 
        raise HTTPException(status_code=403, detail=f"invitation with ID '{invitation_id}' not addressed to user with ID '{credentials[\"user_id\"]'")

    if invitation.status != model.InvitationStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"invitation with ID '{invitation_id}' already has '{invitation.status.value}' status")

    await crud.decline_invitation(invitation_id)
    return dict[message: "ok"]

