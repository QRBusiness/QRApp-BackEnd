from typing import Any, List, Optional

from beanie import Link
from pydantic import BaseModel, Field

from app.models import Area, Branch, Business, Request, ServiceUnit, User
from app.models.order import OrderStatus
from app.schema import BaseResponse
from app.schema.area import AreaResponse
from app.schema.branch import BranchResponse
from app.schema.service_unit import ServiceUnitResponse


class OrderCreate(BaseModel):
    # General info
    items: List = Field(default_factory=list,description="Danh sách món")
    amount: float = Field(default=None,description="Tổng bill")
    # Business info
    business: Link[Business] = Field(...)
    branch: Link[Branch] = Field(...)
    area: Link[Area] = Field(...)
    service_unit: Link[ServiceUnit] = Field(...)
    staff: Link[User] = Field(...)
    request: Link[Request] = Field(...)

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = Field(default=None)

class OrderResponse(BaseResponse):
    items: List[Any]
    branch: BranchResponse
    area: AreaResponse
    service_unit: ServiceUnitResponse