from typing import Optional

from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models import Business

from .base import Base


class Payment(Base):
    business: Optional["Link[Business]"] = Field(default=None, description="Chủ sở hữu")  # type: ignore  # noqa: F821
    accountNo: str = Field(
        ...,
        min_length=6,
        max_length=19,
        description="Số tài khoản ngân hàng",
    )
    accountName: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=50,
        description="Tên tài khoản ngân hàng",
    )
    acqId: int = Field(..., ge=100000, le=999999, description="Mã định danh ngân hàng")

    class Settings:
        indexes = [
            IndexModel([("name", 1)], unique=True),
        ]
