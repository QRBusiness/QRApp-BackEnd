from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.schema import BaseResponse
from app.schema.branch import BranchResponse
from app.schema.business import BusinessResponse


class AreaCreate(BaseModel):
    name: str
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    branch: PydanticObjectId


class AreaUpdate(BaseModel):
    name: Optional[str] = Field(None)
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)


class AreaResponse(BaseResponse):
    name: str
    description: Optional[str] = Field(None)
    image_url: Optional[str] = Field(None)
    branch: Optional[BranchResponse] = Field(None)


class FullAreaResponse(BaseResponse):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    branch: BranchResponse
    business: BusinessResponse
