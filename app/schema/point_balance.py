from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.schema import BaseResponse


class PointBalanceCreate(BaseModel):
    phone: str = Field(...)
    balance: float = Field(...)
    business: PydanticObjectId = Field(...)


class PointBalanceUpdate(BaseModel):
    balance: float = Field(...)


class PointBalanceResponse(BaseResponse):
    phone: str = Field(...)
    balance: float = Field(...)
