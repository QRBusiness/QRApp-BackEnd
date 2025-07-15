from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.api_message import KeyResponse, get_message
from app.common.http_exception import (
    HTTP_401_UNAUTHORZIED,
    HTTP_403_FORBIDDEN,
)
from app.core.security import ACCESS_JWT
from app.db import SessionManager

security = HTTPBearer(auto_error=False)


def login_required(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> bool:
    if credentials is None:
        raise HTTP_401_UNAUTHORZIED(
            error=KeyResponse.UNAUTHORIZED,
            message=get_message(KeyResponse.UNAUTHORIZED),
        )
    if credentials.scheme.lower() != "bearer":
        raise HTTP_401_UNAUTHORZIED(
            error=KeyResponse.INVALID_TOKEN,
            message=get_message(KeyResponse.INVALID_TOKEN),
        )
    try:
        payload: dict = ACCESS_JWT.decode(credentials.credentials)
        if not SessionManager.get(payload.get("user_id")):
            raise HTTP_401_UNAUTHORZIED(
                error=KeyResponse.SESSION_EXPIRED,
                message=get_message(KeyResponse.SESSION_EXPIRED),
            )
        for key, value in payload.items():
            if key == "exp":
                continue
            setattr(request.state, key, value)
        return True
    except Exception as e:
        raise HTTP_401_UNAUTHORZIED(
            error=KeyResponse.INVALID_TOKEN,
            message=get_message(KeyResponse.INVALID_TOKEN),
        ) from e


def required_role(role: List[str] = None):
    def role_checker(request: Request):
        user_role = request.state.user_role
        if role is not None and user_role not in role:
            raise HTTP_403_FORBIDDEN(get_message(KeyResponse.PERMISSION_DENIED))
        return True

    return role_checker


def required_permissions(permissions: List[int] = None) -> bool:
    def permission_checker(request: Request):
        user_permissions: List[int] = request.state.user_permissions
        if permissions is not None:
            if not all(perm in user_permissions for perm in permissions):
                raise HTTP_403_FORBIDDEN(get_message(KeyResponse.PERMISSION_DENIED))
        return True

    return permission_checker


__all__ = ["login_required", "required_role", "required_permissions"]
