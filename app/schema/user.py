from typing import List, Literal, Optional

from beanie import Link, PydanticObjectId
from pydantic import BaseModel, Field, computed_field

from app.models import Business, Group, Permission
from app.schema import BaseResponse
from app.schema.business import BusinessResponse
from app.schema.group import GroupResponse
from app.schema.permission import DetailPermissionResponse


class Auth(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str


class Session(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    old_password: str
    new_password: str


class UserCreate(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    image_url: Optional[str] = None
    role: Literal["Admin", "BusinessOwner", "Staff"] = "Staff"
    permissions: List[Link[Permission]] = Field(
        default_factory=list,
    )
    group: Link[Group] = None
    scope: Optional[Link[Business]] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Administrator(Auth):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @computed_field(return_type=str)
    @property
    def role(self) -> str:
        return "Admin"


class BusinessOwner(Auth):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

    @computed_field(return_type=str)
    @property
    def role(self) -> str:
        return "BusinessOwner"


class Staff(Auth):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    branch: PydanticObjectId

    @computed_field(return_type=str)
    @property
    def role(self) -> str:
        return "Staff"


class BusinessRegister(Auth):
    # owner
    owner_name: Optional[str] = None
    owner_address: Optional[str] = None
    owner_contact: Optional[str] = None
    # business
    business_name: str
    business_address: Optional[str] = None
    business_contact: Optional[str] = None
    business_type: PydanticObjectId
    business_tax_code: Optional[str] = Field(
        default=None, description="Business tax code"
    )

    @computed_field(return_type=str)
    @property
    def role(self) -> str:
        return "BusinessOwner"


class FullUserResponse(BaseResponse):
    username: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    image_url: Optional[str] = None
    role: Optional[str] = None
    permissions: List[DetailPermissionResponse] = []
    group: List[GroupResponse] = []
    business: Optional[BusinessResponse] = None
    available: bool


class UserResponse(BaseResponse):
    username: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    image_url: Optional[str] = None
    role: Optional[str] = None
    available: bool
