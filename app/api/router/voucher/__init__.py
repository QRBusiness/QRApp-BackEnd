from fastapi import APIRouter,Depends,Request
from app.common.api_response import Pagination, Response
from app.schema.voucher import VoucherCreate
from app.service import voucherService
from app.api.dependency import login_required, permission_required

apiRouter = APIRouter(
    tags=["Voucher"],
    prefix="/voucher",
    dependencies = [
        Depends(login_required),
    ],
)


@apiRouter.post(
    path=  "/",
    name = "Tạo khuyến mãi",
    response_model=Response,
    dependencies = [
        Depends(login_required),
    ],
)
async def post_voucher(data: VoucherCreate,request:Request):
    data = data.model_dump()
    data['business'] = request.state.user_scope
    voucher = await voucherService.insert(data)
    return Response(
        data=voucher
    )