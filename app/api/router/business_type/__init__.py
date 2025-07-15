from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query

from app.api.dependency import login_required, required_permissions, required_role
from app.common.api_response import Response
from app.common.http_exception import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.core.config import settings
from app.schema.business import BusinessTypeCreate, BusinessTypeResponse, BusinessTypeUpdate
from app.service import businessService, businessTypeService

apiRouter = APIRouter(
    tags=["Business Type"],
    prefix="/business-type",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["Admin"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem danh sách loại doanh nghiệp",
    response_model=Response[List[BusinessTypeResponse]],
    dependencies=[Depends(required_permissions(permissions=["view.businesstype"]))],
)
async def get_business_type(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    data = await businessTypeService.find_many(
        conditions={},
        skip=(page - 1) * limit,
        limit=limit,
    )
    return Response(data=data)


@apiRouter.post(
    path="",
    name="Tạo loại doanh nghiệp",
    response_model=Response[BusinessTypeResponse],
    dependencies=[Depends(required_permissions(permissions=["create.businesstype"]))],
)
async def post_business_type(data: BusinessTypeCreate | List[BusinessTypeCreate]):
    import re

    if await businessTypeService.find_one({"name": re.compile(f"^{re.escape(data.name)}$", re.IGNORECASE)}):
        raise HTTP_409_CONFLICT(f"{data.name} đã tồn tại")
    data = await businessTypeService.insert(data)
    return Response(data=data)


@apiRouter.put(
    path="/{id}",
    name="Sửa loại Doanh Nghiệp",
    response_model=Response[BusinessTypeResponse],
    dependencies=[Depends(required_permissions(permissions=["update.businesstype"]))],
)
async def update_business_type(id: PydanticObjectId, data: BusinessTypeUpdate):
    if await businessTypeService.find(id) is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if data.name:
        if type := await businessTypeService.find_one({"name": {"$regex": f"^{data.name}$", "$options": "i"}}):
            if type.id != id:
                raise HTTP_409_CONFLICT(f"Loại hình {data.name} đã tồn tại")
    data = await businessTypeService.update(id=id, data=data.model_dump(exclude_none=True))
    return Response(data=data)


@apiRouter.delete(
    path="/{id}",
    name="Xóa loại Doanh Nghiệp",
    deprecated=True,
    dependencies=[Depends(required_permissions(permissions=["delete.businesstype"]))],
)
async def delete_business_type(id: PydanticObjectId):
    type = await businessTypeService.find(id)
    if type is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if await businessService.find_one({"business_type.$id": type.id}):
        raise HTTP_400_BAD_REQUEST("Loại doanh nghiệp đang được sử dụng.")
    if not await businessTypeService.delete(id):
        raise HTTP_400_BAD_REQUEST("Lỗi khi xóa")
    return True
