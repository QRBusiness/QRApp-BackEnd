from app.models.category import Category, SubCategory
from app.schema.category import CategoryCreate, CategoryUpdate, SubCategoryCreate, SubCategoryUpdate
from app.service.base import Service


class CategoryService(Service[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self):
        super().__init__(Category)


class SubCategoryService(Service[SubCategory, SubCategoryCreate, SubCategoryUpdate]):
    def __init__(self):
        super().__init__(SubCategory)


categoryService = CategoryService()
subcategoryService = SubCategoryService()

__all__ = [
    "categoryService",
    "subcategoryService",
]
