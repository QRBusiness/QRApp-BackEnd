from typing import List, Optional

from beanie import Link
from pydantic import BaseModel, Field

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
        default="https://readdy.ai/api/search-image?query=Gourmet avocado toast with poached egg on sourdough bread, topped with cherry tomatoes and microgreens, professional food photography, bright natural lighting, shallow depth of field, appetizing presentation, isolated on light neutral background, high resolution&width=400&height=400&seq=1&orientation=squarish",  # noqa: E501
        description="Ảnh mô tả",
    )
    # Refer - Hỗ trợ lọc
    category: Link[Category]
    subcategory: Link[SubCategory]
    business: Link[Business]
