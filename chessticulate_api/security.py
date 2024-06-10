"""chessticulate.security"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from chessticulate_api import crud
from chessticulate_api.config import CONFIG


async def get_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> dict:
    """Retrieve and validate user JWTs. For use in endpoints as dependency."""
    try:
        decoded_token = jwt.decode(
            credentials.credentials, CONFIG.jwt_secret, [CONFIG.jwt_algo]
        )
    except jwt.exceptions.DecodeError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc
    except jwt.exceptions.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="expired token") from exc
    users = await crud.get_users(id_=decoded_token["user_id"])
    if not users or users[0].deleted:
        raise HTTPException(status_code=401, detail="user has been deleted")
    return decoded_token
