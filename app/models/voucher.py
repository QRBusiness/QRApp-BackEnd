from datetime import datetime
from enum import Enum
from typing import Any, Optional

from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models.business import Business

from .base import Base


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    AMOUNT = "amount"


class Voucher(Base):
    name: str = Field(..., description="Tên voucher")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    conditions: Optional[Any] = Field(default=None, description="Điều kiện áp dụng")
    business: Link[Business] = Field(description="Thuộc doanh nghiệp")
    # Các field cơ bản bổ sung
    code: str = Field(..., description="Mã voucher (dùng để nhập khi áp dụng)")
    discount_type: DiscountType = Field(..., description="Loại giảm giá (percentage/fixed_amount)")
    discount_value: float = Field(..., description="Giá trị giảm giá (ví dụ: 10% hoặc 50000)")
    max_uses: Optional[int] = Field(default=None, description="Số lần sử dụng tối đa")
    used_count: int = Field(default=0, description="Số lần đã sử dụng")
    start_date: datetime = Field(default_factory=datetime.now, description="Ngày bắt đầu hiệu lực")
    end_date: datetime = Field(..., description="Ngày kết thúc hiệu lực")
    is_active: bool = Field(default=True, description="Voucher có đang hoạt động hay không")

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("code", 1),
                    ("business", 1),
                ],
                unique=True,
            ),
        ]
