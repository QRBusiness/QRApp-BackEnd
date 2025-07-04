from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import (login_required, required_permissions,
                                required_role)
from app.common.api_response import Response
from app.common.http_exception import HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.schema.area import AreaCreate, AreaResponse, AreaUpdate
from app.service import areaService, branchService, businessService

apiRouter = APIRouter(
    tags=["Area"],
    prefix="/areas",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["BusinessOwner"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem khu vực",
    status_code=201,
    response_model=Response[List[AreaResponse]],
    dependencies=[Depends(required_permissions(permissions=["view.area"]))],
)
async def view_areas(
    request: Request, branch: Optional[PydanticObjectId] = Query(default=None)
):
    conditions = {
        "business._id": PydanticObjectId(request.state.user_scope),
    }
    if branch:
        conditions["branch._id"] = branch
    areas = await areaService.find_many(
        conditions,
        fetch_links=True,
    )
    return Response(data=areas)


@apiRouter.post(
    path="",
    name="Tạo khu vực",
    status_code=201,
    response_model=Response[AreaResponse],
    dependencies=[Depends(required_permissions(permissions=["create.area"]))],
)
async def post_area(data: AreaCreate, request: Request):
    business = await businessService.find(request.state.user_scope)
    branch = await branchService.find(data.branch)
    if branch is None or branch.business.to_ref().id != business.id:
        raise HTTP_404_NOT_FOUND("Không tìm thấy chi nhánh")
    if await areaService.find_one(
        {"branch.$id": branch.id, "name": {"$regex": f"^{data.name}$", "$options": "i"}}
    ):
        raise HTTP_409_CONFLICT("Khu vực đã tồn tại")
    data = data.model_dump()
    data["business"] = business
    area = await areaService.insert(data)
    await area.fetch_link("branch")
    return Response(data=area)


@apiRouter.put(
    path="/{id}",
    name="Sửa thông tin khu vực",
    status_code=200,
    response_model=Response[AreaResponse],
    dependencies=[Depends(required_permissions(permissions=["update.area"]))],
)
async def put_area(id: PydanticObjectId, data: AreaUpdate, request: Request):
    area = await areaService.find(id)
    if area is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực")
    if area.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực")
    area = await areaService.find_one(
        {
            "branch.$id": area.branch.to_ref().id,
            "name": {"$regex": f"^{data.name}$", "$options": "i"},
        }
    )
    if area is not None and area.id != id:
        raise HTTP_409_CONFLICT("Khu vực đã tồn tại")
    area = await areaService.update(id=id, data=data)
    await area.fetch_link("branch")
    return Response(data=area)


@apiRouter.delete(
    path="/{id}",
    name="Xóa khu vực",
    status_code=200,
    response_model=Response,
    dependencies=[Depends(required_permissions(permissions=["delete.area"]))],
)
async def delete_area(id: PydanticObjectId, request: Request):
    area = await areaService.find(id)
    if area is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực")
    if area.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực trong doanh nghiệp của bạn")
    if not await areaService.delete(id):
        return Response(data="Xóa thất bại")
    return Response(data="Xóa thành công")
