from typing import List, Optional

from beanie import Link
from pydantic import BaseModel, Field
from pymongo import IndexModel

from app.models import Business, Category, SubCategory

from .base import Base


class Option(BaseModel):
    type: str = Field(default="Default")
    price: float = Field(default=0)


class Product(Base):
    name: str = Field(..., description="Tên sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    variants: List[Option] = Field(default_factory=list, description="Các biến thể của sản phẩm")
    options: List[Option] = Field(default_factory=list, description="Các option đi kèm của sản phẩm")
    img_url: Optional[str] = Field(
        default="https://t3.ftcdn.net/jpg/05/79/68/24/360_F_579682465_CBq4AWAFmFT1otwioF5X327rCjkVICyH.jpg",
        description="Ảnh mô tả",
    )
    # Refer - Hỗ trợ lọc
    category: Link[Category]
    subcategory: Link[SubCategory]
    business: Link[Business]

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
