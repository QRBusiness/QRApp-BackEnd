from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, permission_required
from app.common.api_response import Response
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
    path="/",
    name="Danh sách khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(permission_required(permissions=["view.voucher"])),
    ],
)
async def get_vouchers(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=200),
):
    conditions = {"business.$id": PydanticObjectId(request.state.user_scope)}
    vouchers = await voucherService.find_many(
        conditions=conditions,
        skip=(page - 1) * limit,
        limit=limit,
    )
    return Response(data=vouchers)


@apiRouter.get(
    path="/{id}",
    name="Danh sách khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(permission_required(permissions=["view.voucher"])),
    ],
)
async def get_voucher(
    request: Request,
    id: PydanticObjectId,
):
    conditions = {
        "id": id,
        "business.$id": request.state.user_scope,
    }
    voucher = await voucherService.find_one(
        conditions=conditions,
    )
    return Response(data=voucher)


@apiRouter.post(
    path="/",
    name="Tạo khuyến mãi",
    response_model=Response,
    dependencies=[
        Depends(permission_required(permissions=["create.voucher"])),
    ],
)
async def post_voucher(data: VoucherCreate, request: Request):
    data = data.model_dump()
    data["business"] = request.state.user_scope
    voucher = await voucherService.insert(data)
    return Response(data=voucher)
