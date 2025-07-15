from typing import Optional

from beanie import Delete, Link, after_event
from pydantic import Field

from app.models import Business

from .base import Base


class Category(Base):
    name: str = Field(..., description="Phân loại sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    business: Link[Business] = Field(..., description="Thuộc doanh nghiệp nào")

    @after_event(Delete)
    async def delete_category(self):
        from app.service import subcategoryService

        await subcategoryService.delete_many(
            conditions={
                "category.$id": self.id,
            }
        )


class SubCategory(Base):
    name: str = Field(..., description="Phân loại chi tiết sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả (Tùy chọn)")
    category: Link[Category] = Field(..., description="Phân loại chi tiết cho sản phẩm")
    business: Link[Business] = Field(..., description="Thuộc doanh nghiệp")

    @after_event(Delete)
    async def delete_sub_category(self):
        from app.service import productService

        await productService.delete_many(
            conditions={
                "subcategory.$id": self.id,
            }
        )
