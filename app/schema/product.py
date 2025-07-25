from typing import List, Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.models.product import Option
from app.schema import BaseResponse
from app.schema.category import CategoryResponse, SubCategoryResponse


class ProductCreate(BaseModel):
    name: str
    description: Optional[str]
    variants: Optional[List[Option]] = []
    options: Optional[List[Option]] = []
    sub_category: PydanticObjectId


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    variants: Optional[List[Option]] = []
    options: Optional[List[Option]] = []


class ProductResponse(BaseResponse):
    name: str
    description: Optional[str]
    variants: Optional[List[Option]] = []
    options: Optional[List[Option]] = []
    img_url: Optional[str] = None


class FullProductResponse(BaseResponse):
    name: str
    description: Optional[str]
    variants: Optional[List[Option]] = []
    options: Optional[List[Option]] = []
    subcategory: SubCategoryResponse
    category: CategoryResponse
    img_url: Optional[str] = None
    # business: BusinessResponse


# ----------- Import Menu
class ProductInMenu(BaseModel):
    name: str = Field(..., description="Tên sản phẩm")
    description: Optional[str] = Field(default=None, description="Mô tả sản phẩm")
    variants: List[Option] = Field(default_factory=list, description="Danh sách biến thể (vd: Size)")
    options: List[Option] = Field(default_factory=list, description="Tùy chọn thêm (vd: Topping)")
    img_url: Optional[str] = Field(default=None, description="URL hình ảnh minh họa")


class SubCategoryInMenu(BaseModel):
    name: str = Field(..., description="Tên phân loại chi tiết")
    description: Optional[str] = Field(default=None, description="Mô tả phân loại")
    products: List[ProductInMenu] = Field(default_factory=list, description="Danh sách sản phẩm")


class CategoryInMenu(BaseModel):
    name: str = Field(..., description="Tên danh mục")
    description: Optional[str] = Field(default=None, description="Mô tả danh mục")
    subcategories: List[SubCategoryInMenu] = Field(default_factory=list, description="Danh sách phân loại chi tiết")


class Menu(BaseModel):
    categories: List[CategoryInMenu] = Field(default_factory=list)
