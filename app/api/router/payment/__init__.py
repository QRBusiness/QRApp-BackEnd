import httpx
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request

from app.api.dependency import login_required, required_role
from app.common.api_response import Response
from app.common.http_exception import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT
from app.core.decorator import limiter
from app.schema.order import PaymentMethod
from app.schema.payment import PaymentCreate, PaymentResponse
from app.service import paymentService, userService

apiRouter = APIRouter(
    tags=["Payment"],
    prefix="/payment",
    dependencies=[Depends(login_required), Depends(required_role(role=["Admin", "BusinessOwner"]))],
)


@apiRouter.get(path="/banks", name="Danh sách ngân hàng", response_model=Response)
@limiter(duration=120)
async def get_banks(request: Request):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.vietqr.io/v2/banks")
        data = response.json().get("data")
        return Response(data=data)


@apiRouter.get(path="/methods", name="Xem phương thức thanh toán", response_model=Response)
async def get_method():
    return Response(data=[{"name": method.name, "description": method.description()} for method in PaymentMethod])


@apiRouter.get(path="/my-bank", name="Xem thông tin thanh toán", response_model=Response[PaymentResponse])
async def get_my_bank(request: Request):
    payment = await paymentService.find_one(
        conditions={
            "business.$id": PydanticObjectId(request.state.user_scope) if request.state.user_role != "Admin" else None
        }
    )
    return Response(data=payment)


@apiRouter.post(
    path="/banks", name="Thêm tài khoản ngân hàng", status_code=201, response_model=Response[PaymentResponse]
)
async def post_banks(data: PaymentCreate, request: Request):
    payment = await paymentService.find_one(
        {"business.$id": PydanticObjectId(request.state.user_scope) if request.state.user_role != "Admin" else None}
    )
    if payment:
        raise HTTP_409_CONFLICT("Đã có thông tin thanh toán")
    user = await userService.find(request.state.user_id)
    data_dict = data.model_dump(by_alias=False)
    data_dict["business"] = user.business.to_ref() if user.business else None
    payment = await paymentService.insert(data_dict)
    return Response(data=payment)


@apiRouter.delete(path="/my-bank", name="Xóa thông tin thanh toán", response_model=Response[str])
async def delete_my_bank(request: Request):
    payment = await paymentService.find_one(
        conditions={
            "business.$id": PydanticObjectId(request.state.user_scope) if request.state.user_role != "Admin" else None
        }
    )
    if payment is None:
        raise HTTP_400_BAD_REQUEST("Không có thông tin thanh toán")
    if await paymentService.delete(payment.id):
        return Response(data="Xóa thành công")
    return Response(data="Xóa thất bại")
