from typing import List, Literal, Optional

import httpx
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, required_role
from app.common.api_response import Response
from app.common.http_exception import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from app.core.config import settings
from app.schema.order import OrderResponse, OrderStatus, OrderUpdate
from app.service import orderService, paymentService, productService

apiRouter = APIRouter(
    prefix = "/orders",
    tags = ["Order"],
    dependencies = [
        Depends(login_required),
        Depends(required_role(role=['BusinessOwner','Staff']))
    ]
)

@apiRouter.get(
    path = "",
    response_model=Response[List[OrderResponse]]
)
async def get_orders(
    request: Request,
    area: Optional[PydanticObjectId] = Query(default=None),
    service_unit: Optional[PydanticObjectId] = Query(default=None),
    status: Optional[OrderStatus] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions={
        "business._id": PydanticObjectId(request.state.user_scope),
    }
    if request.state.user_branch:
        conditions["branch._id"] = PydanticObjectId(request.state.user_branch)
    if area:
        conditions["area._id"] = area
    if service_unit:
        conditions["service_unit._id"] = service_unit
    if status:
        conditions["status"] = status    
    orders = await orderService.find_many(
        conditions,
        fetch_links=True,
        skip=(page - 1) * limit, 
        limit=limit
    )
    for order in orders:
        for item in order.items:
            product = await productService.find(item.get('product').id)
            item['product'] = product
    return Response(data=orders)

@apiRouter.get(
    path = "/{id}",
    response_model=Response[OrderResponse]
)
async def get_order(
    id: PydanticObjectId,
    request: Request,
):
    conditions={
        "business._id": PydanticObjectId(request.state.user_scope),
        "_id":id,
    }
    order = await orderService.find_one(conditions,fetch_links=True)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn hàng")
    for item in order.items:
        product = await productService.find(item.get('product').id)
        item['product'] = product
    return Response(data=order)

@apiRouter.post(
    path = "/checkout/{id}",
    name = "Checkout order",
    response_model=Response[OrderResponse]
)
async def post_orders(id:PydanticObjectId,request: Request):
    order = await orderService.find(id)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn")
    if order.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    if request.state.user_role != 'BusinessOwner' and order.branch.to_ref().id != PydanticObjectId(request.state.user_branch):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    order = await orderService.update(id,OrderUpdate(status=OrderStatus.PAID))
    for item in order.items:
        product = await productService.find(item.get('product').id)
        item['product'] = product
    await order.fetch_all_links()
    return Response(data=order)

@apiRouter.get(
    path = "/{id}/qrcode",
    name = "Tạo QR Code cho đơn",
    response_model=Response
)
async def gen_qr_for_order(
    id:PydanticObjectId,
    request: Request,
    template: Literal["compact2", "compact", "qr_only", "print"] = Query(default="compact", description="Kiểu template QR cần xuất")
):
    order = await orderService.find(id)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn")
    if order.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    if order.branch.to_ref().id != PydanticObjectId(request.state.user_branch):
        if request.state.user_role != 'BusinessOwner':
            raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    payment = await paymentService.find_one(conditions={
        "business.$id": order.business.to_ref().id
    })
    if payment is None:
        raise HTTP_404_NOT_FOUND("Yêu cầu thêm tài khoản ngân hàng")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url = "https://api.vietqr.io/v2/generate",
            json = {
                "accountNo": payment.accountNo,
                "accountName": payment.accountName,
                "acqId": payment.acqId,
                "amount": order.amount,
                "addInfo": f"Thanh toán đơn hàng {order.id}",
                "format": "text",
                "template": template
            }
        )
        return Response(data=response.json())