from datetime import datetime
from typing import Optional

from beanie import Link, PydanticObjectId
from pydantic import BaseModel, Field, field_validator

from app.models import BusinessType, User
from app.schema import BaseResponse


class BusinessTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None


class BusinessTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BusinessTypeResponse(BaseResponse):
    name: str
    description: Optional[str] = None


class BusinessCreate(BaseModel):
    name: str
    address: str
    contact: str
    business_type: Link[BusinessType]
    tax_code: Optional[str] = None
    owner: Optional[Link[User]] = Field(description="Business Owner")  # type: ignore


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    tax_code: Optional[str] = None

class ExtendBusiness(BaseModel):
    id: PydanticObjectId
    days: int


class FullBusinessResponse(BaseResponse):
    name: str
    address: str
    contact: str
    tax_code: Optional[str] = None
    available: bool
    logo: Optional[str] = None
    business_type: BusinessType
    owner: Optional[User] = Field(description="Business Owner")  # type: ignore
    expired_at: datetime
    @field_validator("owner")
    @classmethod
    def serializer_owner(cls, v: Optional[User]):
        from app.schema.user import UserResponse

        return UserResponse.model_validate(v)


class BusinessResponse(BaseResponse):
    name: str
    address: Optional[str] = None
    contact: Optional[str] = None
    logo: Optional[str] = None
    tax_code: Optional[str] = None
    available: bool
    business_type: BusinessType
    expired_at: datetime
