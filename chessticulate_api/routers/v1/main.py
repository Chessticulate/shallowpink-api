from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr

from chessticulate_api import crud
from chessticulate_api.routers.v1 import schemas

router = APIRouter()

security = HTTPBearer()


async def get_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    try:
        decoded_token = crud.validate_token(credentials.credentials)
    except jwt.exceptions.DecodeError:
        raise HTTPException(status_code=401, detail="invalid token")
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="expired token")
    if not (user := crud.get_users(id_=decoded_token["user_id"])):
        raise HTTPException(status_code=401, detail="user has been deleted")
    return decoded_token


@router.post("/login")
async def login(payload: schemas.LoginRequest) -> schemas.LoginResponse:
    if not (token := await crud.login(payload.name, payload.password)):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"jwt": token}


@router.post("/signup")
async def signup(payload: schemas.CreateUserRequest) -> schemas.CreateUserResponse:
    # this if statement is not properly handling bad credentials
    if not (
        user := await crud.create_user(payload.name, payload.email, payload.password)
    ):
        raise HTTPException(status_code=401, detail="invalid credentials")

    response_data = schemas.CreateUserResponse(
        name=user.name, email=user.email, password=user.password
    )
    return dict(response_data)


@router.get("/user")
async def get_user(
    credentials: Annotated[dict, Depends(get_credentials)],
    user_id: int | None = None,
    user_name: str | None = None,
    skip: int | None = 0,
    limit: int | None = 10,
    order_by: str | None = "date_joined",
    reverse: bool | None = False
    
) -> schemas.GetUserListResponse:

    # retrieving a single user with id or name
    if user_id:
        result = await crud.get_users(id_=user_id)
        return schemas.GetUserListResponse(user_list=[schemas.GetUserResponse(**result[0].__dict__)])

    if user_name:
        result = await crud.get_users(name=user_name)
        return schemas.GetUserListResponse(user_list=[schemas.GetUserResponse(**result[0].__dict__)])
   
    #retrieving a list of users 
    args = {"skip": skip, "limit": limit, "order_by": order_by, "reverse": reverse}

    result = await crud.get_users(**args)
    users = [schemas.GetUserResponse(**user.__dict__) for user in result]
    return schemas.GetUserListResponse(user_list=users)


# user can only delete themselves, can only do so when logged in
@router.delete("/user/delete")
async def delete_user(
    credentials: Annotated[dict, Depends(get_credentials)]
) -> bool:
    user_id = credentials["user_id"]
    deleted_user = await crud.delete_user(user_id)
    if deleted_user is not None:
        return True
    else:
        raise HTTPException(
            status_code=404, detail=f"User with ID '{credentials['user_id']}' not found"
        )


@router.post("/invitation")
async def create_invitation(
    credentials: Annotated[dict, Depends(get_credentials)],
    payload: schemas.CreateInvitationRequest,
) -> schemas.CreateInvitationResponse:
    if not (
        user := await crud.get_users(id_=payload.to_id)
    ):
        raise HTTPException(status_code=400, detail="addressee does not exist")
    
    # I decided that the endpoints should check if a user is deleted or not
    # if get_users cant retrieve deleted users that would defeat the purpose of leaving deleted users in the db 
    if **user.__dict__["deleted"]:
        raise HTTPException(status_code=400, detail="user is deleted")

    result = await crud.create_invitation(credentials["user_id"], payload.to_id)
    print(result.__dict__)
    return schemas.CreateInvitationResponse(**result.__dict__)


# delete_invitation wip
@router.delete("/invitations/{invitation_id}")
async def delete_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], id_
) -> schemas.DeleteInvitationResponse:
    return dict(await crud.delete_invitation(id_, credentials["user_id"]))


@router.get("/invitations")
async def get_invitations(
    credentials: Annotated[dict, Depends(get_credentials)],
    to_id: int | None = None,
    from_id: int | None = None,
    invitation_id: int | None = None,
    status: str | None = None,
    skip: int | None = 10,
    limit: int | None = 1,
    reverse: bool | None = False
) -> schemas.GetInvitationResponse:
    if not (to_id or from_id):
        raise HTTPException(
            status_code=400, detail="'to_id' or 'from_id' must be supplied"
        )
    if from_id != credentials["user_id"] and to_id != credentials["user_id"]:
        raise HTTPException(
            status_code=400,
            detail="'to_id' or 'from_id' must match the requestor's user ID",
        )

    args = {"skip": skip, "limit": limit}
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
async def accept_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int
) -> schemas.AcceptInvitationResponse:
    # if a user is deleted, how are its invitations removed from the Invitations tab

    invitation_list = crud.get_invitations(id_=invitation_id)

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

    # check if user who sent invitation still exists
    if await crud.get_user_by_id(inivtation.from_id) is None:
        raise HTTPException(
            status_code=404,
            deatil=(
                f"user with ID '{invitation.from_id}' who sent invitation with id"
                f" '{invitation_id}' does not exist"
            ),
        )

    if invitation.status != model.InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=(
                f"invitation with ID '{invitation_id}' already has"
                f" '{invitation.status.value}' status"
            ),
        )

    result = await crud.accept_invitation(invitation_id)

    return result.id_


@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(
    credentials: Annotated[dict, Depends(get_credentials)], invitation_id: int
):

    invitation_list = get_invitations(id_=invitation_id)

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

    # check if user who sent invitation still exists
    if await crud.get_user_by_id(inivtation.from_id) is None:
        raise HTTPException(
            status_code=404,
            deatil=(
                f"user with ID '{invitation.from_id}' who sent invitation with id"
                f" '{invitation_id}' does not exist"
            ),
        )

    if invitation.status != model.InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=(
                f"invitation with ID '{invitation_id}' already has"
                f" '{invitation.status.value}' status"
            ),
        )

    await crud.decline_invitation(invitation_id)
    return dict[message:"ok"]


# @router.post("/games/{game_id}/move")


