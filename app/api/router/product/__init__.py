import uuid
from typing import List, Optional

import httpx
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.api.dependency import login_required, permission_required, role_required
from app.common.api_response import Response
from app.common.http_exception import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.core.config import settings
from app.db import QRCode
from app.schema.category import CategoryResponse, SubCategoryResponse
from app.schema.plan import PlanResponse
from app.schema.product import FullProductResponse, ProductCreate, ProductResponse, ProductUpdate
from app.service import categoryService, paymentService, planService, productService, subcategoryService

public_apiRouter = APIRouter(tags=["Resource Public"])


@public_apiRouter.get(path="/plans", response_model=Response[List[PlanResponse]], name="Danh sách gói gia hạn")
async def get_plans():
    payment = await paymentService.find_one({"business.$id": None})
    if payment is None:
        raise HTTP_400_BAD_REQUEST("Hiện tại thanh toán không khả dụng")
    plans = await planService.find_many()
    async with httpx.AsyncClient() as client:
        data = []
        for plan in plans:
            response = await client.post(
                url="https://api.vietqr.io/v2/generate",
                json={
                    "accountNo": payment.accountNo,
                    "accountName": payment.accountName,
                    "acqId": payment.acqId,
                    "amount": plan.price,
                    "addInfo": f"Thanh toán đơn hàng {uuid.uuid4()}",
                    "format": "text",
                    "template": "template",
                },
            )
            plan = plan.model_dump()
            plan["qr_code"] = response.json().get("data").get("qrDataURL")
            data.append(plan)
        return Response(data=data)


@public_apiRouter.get(
    path="/products/{business}",
    name="Xem danh sách sản phẩm (công khai)",
    response_model=Response[List[FullProductResponse]],
)
async def get_products(
    business: PydanticObjectId,
    category: Optional[PydanticObjectId] = Query(default=None),
    sub_category: Optional[PydanticObjectId] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions = {"business._id": business}
    if category:
        conditions["category._id"] = category
    if sub_category:
        conditions["subcategory._id"] = sub_category
    products = await productService.find_many(conditions, skip=(page - 1) * limit, limit=limit, fetch_links=True)
    return Response(data=products)


@public_apiRouter.get(
    path="/category/{business}",
    name="Xem phân loại sản phẩm (công khai)",
    response_model=Response[List[CategoryResponse]],
)
async def get_categories(
    business: PydanticObjectId,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions = {"business.$id": business}
    categories = await categoryService.find_many(
        conditions=conditions,
        skip=(page - 1) * limit,
        limit=limit,
        projection_model=CategoryResponse,
    )
    return Response(data=categories)


@public_apiRouter.get(
    path="/sub-category/{business}",
    name="Xem phân loại chi tiết sản phẩm (công khai)",
    response_model=Response[List[SubCategoryResponse]],
)
async def get_subcategories(
    business: PydanticObjectId,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    categories = await categoryService.find_many({"business.$id": business})
    conditions = {"category._id": {"$in": [category.id for category in categories]}}
    sub_categories = await subcategoryService.find_many(
        conditions=conditions, skip=(page - 1) * limit, limit=limit, fetch_links=True
    )
    return Response(data=sub_categories)


private_apiRouter = APIRouter(
    tags=["Product"],
    prefix="/products",
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["BusinessOwner", "Staff"])),
    ],
)


@private_apiRouter.get(
    path="",
    name="Xem danh sách sản phẩm",
    status_code=200,
    response_model=Response[List[FullProductResponse]],
    dependencies=[Depends(permission_required(permissions=["view.product"]))],
)
async def get_product(
    request: Request,
    category: Optional[PydanticObjectId] = Query(default=None),
    sub_category: Optional[PydanticObjectId] = Query(default=None),
):
    conditions = {"business._id": PydanticObjectId(request.state.user_scope)}
    if category:
        conditions["category._id"] = category
    if sub_category:
        conditions["subcategory._id"] = sub_category
    products = await productService.find_many(conditions, fetch_links=True)
    return Response(data=products)


@private_apiRouter.post(
    path="",
    name="Sản phẩm",
    status_code=201,
    response_model=Response[ProductResponse],
    dependencies=[Depends(permission_required(permissions=["create.product"]))],
)
async def post_product(data: ProductCreate, request: Request):
    subcategory = await subcategoryService.find(data.sub_category)
    if subcategory is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    if product := await productService.find_one(conditions={"subcategory.$id": subcategory.id, "name": data.name}):
        raise HTTP_409_CONFLICT(f"Món {data.name} đã có trong Menu")
    await subcategory.fetch_link("category")
    category = subcategory.category
    business = category.business
    if business.id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy phân loại")
    data = data.model_dump()
    data["category"] = category
    data["subcategory"] = subcategory
    data["business"] = business
    product = await productService.insert(data)
    return Response(data=product)


@private_apiRouter.post(
    path="/image/{id}",
    name="Thêm ảnh cho sản phẩm",
    status_code=200,
    response_model=Response[ProductResponse],
    dependencies=[Depends(permission_required(permissions=["update.product"]))],
)
async def post_image_product(
    request: Request,
    id: PydanticObjectId,
    image: UploadFile = File(...),
):
    product = await productService.find(id)
    if product is None or product.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy sản phẩm")
    contents = await image.read()
    object_name = QRCode.upload(
        object=contents,
        object_name=f"product_{id}_{image.filename}",
        content_type=image.content_type,
    )
    product = await productService.update(id, {"img_url": QRCode.get_url(object_name)})
    return Response(data=product)


@private_apiRouter.put(
    path="/{id}",
    name="Sửa thông tin sản phẩm",
    status_code=201,
    response_model=Response[ProductResponse],
    dependencies=[Depends(permission_required(permissions=["update.product"]))],
)
async def put_product(id: PydanticObjectId, data: ProductUpdate, request: Request):
    product = await productService.find(id)
    if product is None or product.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy sản phẩm")
    product = await productService.update(id, data)
    return Response(data=product)


@private_apiRouter.delete(
    path="/{id}",
    name="Xóa sản phẩm",
    status_code=200,
    response_model=Response,
    dependencies=[Depends(permission_required(permissions=["delete.product"]))],
)
async def delete_product(id: PydanticObjectId, request: Request):
    product = await productService.find(id)
    if product is None or product.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy sản phẩm")
    if not await productService.delete(id):
        raise HTTP_400_BAD_REQUEST("Xóa thất bại")
    return Response(data="Xóa thành công")
