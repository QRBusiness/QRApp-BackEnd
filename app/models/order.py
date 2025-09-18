from enum import Enum
from typing import List, Optional

from beanie import Link
from pydantic import Field

from .base import Base


class PaymentMethod(str, Enum):
    CASH = "Cash"
    BANK = "Bank"

    def description(self) -> str:
        return {
            PaymentMethod.CASH: "Tiền mặt",
            PaymentMethod.BANK: "Chuyển khoản",
        }[self]


class OrderStatus(str, Enum):
    PREPARING = "Preparing"
    UNPAID = "Unpaid"
    PAID = "Paid"

    def next(self) -> "OrderStatus":
        flow = {
            OrderStatus.PREPARING: OrderStatus.UNPAID,
            OrderStatus.UNPAID: OrderStatus.PAID,
            OrderStatus.PAID: OrderStatus.PAID,
        }
        return flow[self]


class Order(Base):
    # General info
    items: List = Field(default_factory=list, description="Danh sách món")
    amount: float = Field(...)
    status: OrderStatus = Field(default=OrderStatus.PREPARING)
    # Business info
    business: "Link[Business]" = Field(...)  # type: ignore  # noqa: F821
    branch: "Link[Branch]" = Field(...)  # type: ignore  # noqa: F821
    area: "Link[Area]" = Field(...)  # type: ignore  # noqa: F821
    service_unit: "Link[ServiceUnit]" = Field(...)  # type: ignore  # noqa: F821
    staff: "Link[User]" = Field(...)  # type: ignore # noqa: F821
    request: "Link[Request]" = Field(...)  # type: ignore # noqa: F821
    # Payment Method
    payment_method: PaymentMethod = Field(default=PaymentMethod.CASH)


class ExtendOrder(Base):
    business: "Link[Business]" = Field(description="Doanh nghiệp muốn gia hạn")  # type: ignore  # noqa: F821
    plan: Optional["Link[Plan]"] = Field(default=None, description="Gói gia hạn")  # type: ignore  # noqa: F821
    image: str = Field(..., description="Ảnh xác minh thanh toán")
    payment_method: PaymentMethod = Field(default=PaymentMethod.BANK)
    status: OrderStatus = Field(default=OrderStatus.UNPAID)
