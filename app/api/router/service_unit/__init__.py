from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.api.dependency import (login_required, required_permissions,
                                required_role)
from app.common.api_response import Response
from app.common.http_exception import HTTP_404_NOT_FOUND
from app.db import QRCode
from app.schema.service_unit import ServiceUnitResponse, ServiceUnitUpdate
from app.service import areaService, unitService

apiRouter = APIRouter(
    tags=["Service Unit"],
    prefix="/services",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["BusinessOwner","Staff"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem đơn vị dịch vụ",
    response_model=Response[List[ServiceUnitResponse]],
    dependencies=[
        Depends(required_permissions(permissions=[
            "view.serviceunit"
        ]))
    ]
)
async def get_service(
    request: Request,
    branch: Optional[PydanticObjectId] = Query(
        default=None, description="Lọc đơn vị theo chi nhánh"
    ),
    area: Optional[PydanticObjectId] = Query(
        default=None, description="Lọc đơn vị theo khu vực"
    ),
):
    areas = await areaService.find_many(
        conditions={"business.$id": PydanticObjectId(request.state.user_scope)}
    )
    areas = [area.to_ref().id for area in areas]
    conditions = {"area._id": {"$in": [area] if area else areas}}
    services = await unitService.find_many(conditions, fetch_links=True)
    if branch:
        services = [service for service in services if service.area.branch.id == branch]
    return Response(data=services)


@apiRouter.post(
    path="",
    name="Tạo đơn vị dịch vụ",
    status_code=201,
    response_model=Response[ServiceUnitResponse],
    dependencies=[
        Depends(required_permissions(permissions=[
            "create.serviceunit"
        ]))
    ]
)
async def post_service(
    request: Request,
    name: str = Form(),
    area: PydanticObjectId = Form(),
    qr_code: Optional[UploadFile] = File(default=None),
):
    area = await areaService.find(area)
    if area is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực trong doanh nghiệp của bạn")
    if PydanticObjectId(request.state.user_scope) != area.business.to_ref().id:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khu vực trong doanh nghiệp của bạn")
    if qr_code:
        contents = await qr_code.read()
        object_name = QRCode.upload(
            object=contents,
            object_name=f"{request.state.user_id}_{qr_code.filename}",
            content_type=qr_code.content_type,
        )
        qr_link = QRCode.get_url(object_name)
    else:
        qr_link = None
    data = await unitService.insert({
        "name": name,
        "area": area,
        "qr_code": qr_link,
        "branch": area.branch,
    })
    await data.fetch_link('area')
    await data.area.fetch_link("branch")
    return Response(data=data)


@apiRouter.put(
    path="/{id}",
    name="Cập nhật đơn vị dịch vụ",
    response_model=Response[ServiceUnitResponse],
    dependencies=[
        Depends(required_permissions(permissions=[
            "update.serviceunit"
        ]))
    ]
)
async def put_service(id: PydanticObjectId, data: ServiceUnitUpdate, request: Request):
    service_unit = await unitService.find(id)
    if service_unit is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    area = await areaService.find(service_unit.area.to_ref().id)
    if PydanticObjectId(request.state.user_scope) != area.business.to_ref().id:
        raise HTTP_404_NOT_FOUND("Không tìm thấy dịch vụ trong doanh nghiệp của bạn")
    service = await unitService.update(
        id=id,
        data=data,
    )
    await service.fetch_link("area")
    return Response(data=service)


@apiRouter.post(
    path="/{id}",
    name="Cập nhật QRCode",
    response_model=Response[ServiceUnitResponse],
)
async def post_qrcode(id: PydanticObjectId, qr_code: UploadFile = File(...)):
    contents = await qr_code.read()
    object_name = QRCode.upload(
        object=contents,
        object_name=f"{id}_{qr_code.filename}",
        content_type=qr_code.content_type,
    )
    service = await unitService.update(
        id=id, data={"qr_code": QRCode.get_url(object_name)}
    )
    await service.fetch_link("area")
    return Response(data=service)


@apiRouter.delete(
    path="/{id}",
    name="Xóa đơn vị dịch vụ",
    response_model=Response,
    dependencies=[
        Depends(required_permissions(permissions=[
            "delete.serviceunit"
        ]))
    ]
)
async def delete_service(id: PydanticObjectId, request: Request):
    service_unit = await unitService.find(id)
    if service_unit is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    area = await areaService.find(service_unit.area.to_ref().id)
    if PydanticObjectId(request.state.user_scope) != area.business.to_ref().id:
        raise HTTP_404_NOT_FOUND("Không tìm thấy dịch vụ trong doanh nghiệp của bạn")
    if not await unitService.delete(id):
        return Response(data="Xóa thất bại")
    return Response(data="Xóa thành công")
