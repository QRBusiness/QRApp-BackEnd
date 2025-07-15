from typing import List, Optional

from pydantic import BaseModel

from app.schema import BaseResponse


class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(BaseResponse):
    name: str
    description: Optional[str] = None


class SubCategoryResponse(BaseResponse):
    name: str
    description: Optional[str] = None
    category: CategoryResponse


class FullCategoryResponse(BaseResponse):

    name: str
    description: Optional[str] = None
    sub_category: List[SubCategoryResponse] = []
