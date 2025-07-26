from typing import Any, List, Optional

from beanie import Link
from pydantic import BaseModel, Field

from app.models import Area, Branch, Business, Plan, Request, ServiceUnit, User
from app.models.order import OrderStatus, PaymentMethod
from app.schema import BaseResponse
from app.schema.area import AreaResponse
from app.schema.branch import BranchResponse
from app.schema.business import BusinessResponse
from app.schema.request import MinimumResquestResponse
from app.schema.service_unit import ServiceUnitResponse


class OrderCreate(BaseModel):
    # General info
    items: List = Field(default_factory=list, description="Danh sách món")
    amount: float = Field(default=None, description="Tổng bill")
    # Business info
    business: Link[Business] = Field(...)
    branch: Link[Branch] = Field(...)
    area: Link[Area] = Field(...)
    service_unit: Link[ServiceUnit] = Field(...)
    staff: Link[User] = Field(...)
    request: Link[Request] = Field(...)
    # Payment method:
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH)


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = Field(default=None)
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH)


class MinimumOrderResponse(BaseResponse):
    items: List[Any]
    amount: float
    status: OrderStatus


class OrderResponse(BaseResponse):
    items: List[Any]
    status: OrderStatus
    branch: BranchResponse
    area: AreaResponse
    service_unit: ServiceUnitResponse
    request: MinimumResquestResponse
    payment_method: PaymentMethod


class Report(BaseModel):
    orders: List[OrderResponse]
    total_amount: float
    total_count: int


class ExtenOrderCreate(BaseModel):
    business: Business
    plan: Plan
    image: str


class ExtenOrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None


class ExtenOrderResponse(BaseModel):
    business: BusinessResponse
    plan: Plan
    status: Optional[OrderStatus] = None


class CheckoutOrder(BaseModel):
    orders: List[MinimumOrderResponse]
    qr_code: str
