from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query

from app.api.dependency import login_required, role_required
from app.common.api_response import Pagination, Response
from app.common.http_exception import HTTP_404_NOT_FOUND
from app.core.config import settings
from app.schema.permission import FullPermissionResponse, PermissionUpdate
from app.service import permissionService

apiRouter = APIRouter(
    tags=["Permission"],
    prefix="/permissions",
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["Admin"])),
    ],
)


@apiRouter.get(
    path="",
    name="Danh sách quyền",
    status_code=200,
    response_model=Response[List[FullPermissionResponse]],
)
async def get_permissions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions = {}
    permissions = await permissionService.find_many(
        conditions,
        skip=(page - 1) * limit,
        limit=limit,
    )
    return Response(
        data=permissions,
        pagination=Pagination(current_page=page, per_page=limit, total_items=await permissionService.count(conditions)),
    )


@apiRouter.get(
    path="/{id}",
    name="Quyền hạn",
    status_code=200,
    response_model=Response[FullPermissionResponse],
)
async def get_permission(id: PydanticObjectId):
    permission = await permissionService.find(id)
    if permission is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    return Response(data=permission)


@apiRouter.put(
    path="/{id}",
    name="Quyền hạn",
    status_code=200,
    response_model=Response[FullPermissionResponse],
)
async def put_permission(id: PydanticObjectId, data: PermissionUpdate):
    permission = await permissionService.find(id)
    if permission is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    permission = await permissionService.update(id=id, data=data)
    return Response(data=permission)
