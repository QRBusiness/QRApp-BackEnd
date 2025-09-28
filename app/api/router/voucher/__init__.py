from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, permission_required
from app.common.api_response import Pagination, Response
from app.common.http_exception import HTTP_404_NOT_FOUND
from app.core.config import settings
from app.schema.voucher import VoucherCreate
from app.service import voucherService

apiRouter = APIRouter(
    tags=["Voucher"],
    prefix="/voucher",
    dependencies=[
        Depends(login_required),
    ],
)


@apiRouter.get(
    path="",
    name="Danh sách khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.voucher"],
            ),
        ),
    ],
)
async def get_vouchers(
    request: Request,
    min_points: float = Query(default=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=200),
):
    conditions = {
        "business.$id": PydanticObjectId(request.state.user_scope),
        "required_points": {
            "$gte": min_points,
        },
    }
    vouchers = await voucherService.find_many(
        conditions=conditions,
        skip=(page - 1) * limit,
        limit=limit,
    )
    return Response(
        data=vouchers,
        pagination=Pagination(
            current_page=page,
            per_page=limit,
            total_items=await voucherService.count(conditions),
        ),
    )


@apiRouter.get(
    path="/{id}",
    name="Xem khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.voucher"],
            ),
        ),
    ],
)
async def get_voucher(
    request: Request,
    id: PydanticObjectId,
):
    conditions = {
        "_id": id,
        "business.$id": PydanticObjectId(request.state.user_scope),
    }
    voucher = await voucherService.find_one(
        conditions=conditions,
    )
    if voucher is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khuyến mãi")
    return Response(data=voucher)


@apiRouter.post(
    path="",
    name="Tạo khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(
            permission_required(
                permissions=["create.voucher"],
            ),
        ),
    ],
)
async def post_voucher(data: VoucherCreate, request: Request):
    data = data.model_dump()
    data["business"] = request.state.user_scope
    voucher = await voucherService.insert(data)
    return Response(data=voucher)


@apiRouter.delete(
    path="/{id}",
    name="Xóa khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.voucher"],
            ),
        ),
    ],
)
async def delete_voucher(
    request: Request,
    id: PydanticObjectId,
):
    conditions = {
        "_id": id,
        "business.$id": PydanticObjectId(request.state.user_scope),
    }
    voucher = await voucherService.find_one(
        conditions=conditions,
    )
    if voucher is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy khuyến mãi")
    if not await voucherService.delete(id):
        return Response(data="Xóa thất bại")
    return Response(data="Xóa thành công")
