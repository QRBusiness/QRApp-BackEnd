from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.voucher import DiscountType


class VoucherCreate(BaseModel):
    name: str = Field(...)
    description: Optional[str] = None
    conditions: Optional[Any] = None
    # Các field cơ bản bổ sung
    required_points: int = Field(...)
    discount_type: DiscountType = Field(default=DiscountType.PERCENTAGE)
    discount_value: float = Field(...)
    discount_max: Optional[float] = None
    max_uses: Optional[int] = None
    start_date: datetime = Field(default_factory=datetime.now)
    end_date: Optional[datetime] = None
    is_active: bool = Field(default=True)


class VoucherUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Any] = None
    # Các field cơ bản bổ sung
    required_points: Optional[int] = None
    discount_type: Optional[DiscountType] = None
    discount_value: Optional[float] = None
    discount_max: Optional[float] = None
    max_uses: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
