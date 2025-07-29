from typing import Optional

from pydantic import BaseModel

from app.schema import BaseResponse


class PermissionCreate(BaseModel):
    code: str
    description: Optional[str] = None


class PermissionUpdate(BaseModel):
    description: Optional[str] = None


class FullPermissionResponse(BaseResponse):
    code: str
    description: Optional[str] = None


class DetailPermissionResponse(BaseResponse):
    code: str
    description: Optional[str] = None


class PermissionProjection(BaseModel):
    code: str
