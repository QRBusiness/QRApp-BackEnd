from typing import Optional

from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models import Business

from .base import Base


class Category(Base):
    name: str = Field(..., description="Phân loại sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    business: Link[Business] = Field(..., description="Thuộc doanh nghiệp nào")

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("name", 1),
                    ("business", 1),
                ],
                unique=True,
            )
        ]


class SubCategory(Base):
    name: str = Field(..., description="Phân loại chi tiết sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    category: Link[Category] = Field(..., description="Phân loại chi tiết cho sản phẩm")
    business: Link[Business] = Field(..., description="Thuộc doanh nghiệp")

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("name", 1),
                    ("category", 1),
                    ("business", 1),
                ],
                unique=True,
            )
        ]
