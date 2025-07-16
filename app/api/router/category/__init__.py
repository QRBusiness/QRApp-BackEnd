from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, permission_required, role_required
from app.common.api_response import Response
from app.common.http_exception import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.db import Mongo
from app.schema.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    FullCategoryResponse,
    SubCategoryCreate,
    SubCategoryResponse,
    SubCategoryUpdate,
)
from app.service import businessService, categoryService, productService, subcategoryService

apiRouter = APIRouter(
    tags=["Category"],
    prefix="/categories",
    dependencies=[
        Depends(login_required),
        Depends(
            role_required(
                role=[
                    "BusinessOwner",
                    "Staff",
                ],
            ),
        ),
    ],
)


@apiRouter.post(
    path="",
    name="Phân loại sản phẩm",
    status_code=201,
    response_model=Response[CategoryResponse],
    dependencies=[Depends(permission_required(permissions=["create.category"]))],
)
async def post_category(data: CategoryCreate, request: Request):
    business = await businessService.find(request.state.user_scope)
    if await categoryService.find_one(conditions={"name": data.name, "business.$id": business.id}):
        raise HTTP_409_CONFLICT(f"Phân loại {data.name} đã tồn tại")
    data = data.model_dump()
    data["business"] = business
    category = await categoryService.insert(data)
    return Response(data=category)


@apiRouter.get(
    path="",
    name="Xem tất cả phân loại",
    status_code=200,
    response_model=Response[List[CategoryResponse]],
    dependencies=[Depends(permission_required(permissions=["view.category"]))],
)
async def get_subcategory(request: Request):
    categories = await categoryService.find_many(
        conditions={"business.$id": PydanticObjectId(request.state.user_scope)}
    )
    return Response(data=categories)


@apiRouter.get(
    path="/subcategory",
    name="Xem tất cả chi tiết phân loại",
    status_code=200,
    response_model=Response[List[SubCategoryResponse]],
    dependencies=[Depends(permission_required(permissions=["view.subcategory"]))],
)
async def get_category(request: Request, category: Optional[PydanticObjectId] = Query(default=None)):
    if category:
        category = await categoryService.find(category)
        if category is None:
            raise HTTP_404_NOT_FOUND("Phân loại không phù hợp")
        categories = [category]
    else:
        categories = await categoryService.find_many(
            conditions={"business.$id": PydanticObjectId(request.state.user_scope)}
        )
    subcategories = await subcategoryService.find_many(
        conditions={
            "category._id": {"$in": [cat.id for cat in categories]},
        },
        fetch_links=True,
    )
    return Response(data=subcategories)


@apiRouter.put(
    path="/subcategory/{id}",
    name="Chỉnh sửa chi tiết phân loại",
    status_code=200,
    response_model=Response[SubCategoryResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=[
                    "update.subcategory",
                ],
            ),
        ),
    ],
)
async def put_sub_category(id: PydanticObjectId, data: SubCategoryUpdate, request: Request):
    sub_category = await subcategoryService.find(id)
    if sub_category is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    await sub_category.fetch_link("category")
    if sub_category.category.business.id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    subcat = await subcategoryService.update(id, data)
    await subcat.fetch_link("category")
    return Response(data=subcat)


@apiRouter.get(
    path="/{id}",
    name="Xem một phân loại",
    status_code=200,
    response_model=Response[FullCategoryResponse],
    dependencies=[Depends(permission_required(permissions=["view.subcategory"]))],
)
async def view_category(id: PydanticObjectId, request: Request):
    category = await categoryService.find_one(
        conditions={
            "_id": id,
            "business.$id": PydanticObjectId(request.state.user_scope),
        },
    )
    if category is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    sub_categories = await subcategoryService.find_many(
        {"category._id": PydanticObjectId(category.id)},
        fetch_links=True,
        projection_model=SubCategoryResponse,
    )
    category = category.model_dump()
    category["sub_category"] = sub_categories
    return Response(data=category)


@apiRouter.put(
    path="/{id}",
    name="Chỉnh sửa phân loại",
    status_code=200,
    response_model=Response[CategoryResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=[
                    "update.category",
                ],
            ),
        ),
    ],
)
async def put_category(id: PydanticObjectId, data: CategoryUpdate, request: Request):
    category = await categoryService.find_one(
        conditions={
            "_id": id,
            "business.$id": PydanticObjectId(request.state.user_scope),
        },
        projection_model=CategoryResponse,
    )
    if category is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    category = await categoryService.update(id=category.id, data=data)
    return Response(data=category)


@apiRouter.delete(
    path="/{id}",
    name="Xóa phân loại",
    status_code=200,
    response_model=Response[str],
    dependencies=[Depends(permission_required(permissions=["delete.category"]))],
)
async def delete_category(id: PydanticObjectId, request: Request):
    async with categoryService.transaction(Mongo.client) as session:
        category = await categoryService.find_one(
            conditions={
                "_id": id,
                "business.$id": PydanticObjectId(request.state.user_scope),
            },
            session=session,
        )
        if category is None:
            raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
        await categoryService.delete(id)
        await subcategoryService.delete_many(conditions={"category.$id": id})
        await productService.delete_many(conditions={"category.$id": id})
    return Response(data="Xóa thành công")


@apiRouter.post(
    path="/{id}/subcategory",
    name="Phân loại chi tiết",
    status_code=201,
    response_model=Response[SubCategoryResponse],
    dependencies=[Depends(permission_required(permissions=["create.subcategory"]))],
)
async def post_subcategory(id: PydanticObjectId, data: SubCategoryCreate, request: Request):
    category = await categoryService.find_one(
        conditions={
            "_id": id,
            "business.$id": PydanticObjectId(request.state.user_scope),
        }
    )
    if category is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    data = data.model_dump()
    data["category"] = category
    data["business"] = category.business
    sub_category = await subcategoryService.insert(data)
    return Response(data=sub_category)


@apiRouter.delete(
    path="/{id}/subcategory",
    name="Xóa phân loại chi tiết",
    status_code=200,
    response_model=Response[str],
    dependencies=[Depends(permission_required(permissions=["delete.subcategory"]))],
)
async def delete_subcategory(id: PydanticObjectId, request: Request):
    async with subcategoryService.transaction(Mongo.client) as session:
        sub_category = await subcategoryService.find(id, session=session)
        if sub_category is None:
            raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
        await sub_category.fetch_link("category")
        category = sub_category.category
        if category.business.id != PydanticObjectId(request.state.user_scope):
            raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
        await subcategoryService.delete(id)
        await productService.delete_many(conditions={"subcategory.$id": id})
    return Response(data="Xóa thành công")
