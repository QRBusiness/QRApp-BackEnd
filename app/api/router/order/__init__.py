from typing import List, Literal, Optional

import httpx
from beanie import Link, PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, permission_required, role_required
from app.common.api_response import Response
from app.common.http_exception import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from app.core.config import settings
from app.schema.area import AreaResponse
from app.schema.branch import BranchResponse
from app.schema.order import OrderResponse, OrderStatus, OrderUpdate, PaymentMethod
from app.schema.service_unit import ServiceUnitResponse
from app.service import orderService, paymentService, productService

apiRouter = APIRouter(
    prefix="/orders",
    tags=["Order"],
    dependencies=[
        Depends(login_required),
        Depends(
            role_required(
                role=[
                    "BusinessOwner",
                    "Staff",
                ],
            ),
        ),
    ],
)


@apiRouter.get(
    path="",
    response_model=Response[List[OrderResponse]],
    name="Danh sách đơn",
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.order"],
            ),
        ),
    ],
)
async def get_orders(
    request: Request,
    area: Optional[PydanticObjectId] = Query(default=None),
    service_unit: Optional[PydanticObjectId] = Query(default=None),
    branch: Optional[PydanticObjectId] = Query(default=None),
    status: Optional[OrderStatus] = Query(default=None),
    method: Optional[PaymentMethod] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions = {
        "business._id": PydanticObjectId(request.state.user_scope),
    }
    if request.state.user_branch:
        conditions["branch._id"] = PydanticObjectId(request.state.user_branch)
    else:
        if branch:
            conditions["branch._id"] = branch
    if area:
        conditions["area._id"] = area
    if service_unit:
        conditions["service_unit._id"] = service_unit
    if status:
        conditions["status"] = status
    if method:
        conditions["payment_method"] = method
    orders = await orderService.find_many(
        conditions,
        fetch_links=True,
        skip=(page - 1) * limit,
        limit=limit,
    )
    for order in orders:
        for item in order.items:
            product = await productService.find(item.get("product").id)
            item["product"] = product
    for order in orders:
        if isinstance(order.service_unit, Link):
            order.service_unit = ServiceUnitResponse(id=order.service_unit.to_dict().get("id"), name="Không xác định")
        if isinstance(order.area, Link):
            order.area = AreaResponse(
                id=order.area.to_dict().get("id"),
                name="Không xác định",
                branch=(
                    BranchResponse(
                        id=order.branch.to_dict().get("id"),
                        name="Không xác định",
                        address="Không xác định",
                    )
                    if isinstance(order.branch, Link)
                    else order.branch
                ),
            )
        if isinstance(order.branch, Link):
            order.branch = BranchResponse(
                id=order.branch.to_dict().get("id"), name="Không xác định", address="Không xác định"
            )
    return Response(data=orders)


@apiRouter.get(
    path="/{id}",
    response_model=Response[OrderResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.order"],
            ),
        ),
    ],
)
async def get_order(
    id: PydanticObjectId,
    request: Request,
):
    conditions = {
        "business._id": PydanticObjectId(request.state.user_scope),
        "_id": id,
    }
    order = await orderService.find_one(conditions, fetch_links=True)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn hàng")
    for item in order.items:
        product = await productService.find(item.get("product").id)
        item["product"] = product
    return Response(data=order)


@apiRouter.post(
    path="/checkout/{id}",
    name="Checkout order",
    response_model=Response[OrderResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=["update.order"],
            ),
        ),
    ],
)
async def post_orders(
    id: PydanticObjectId,
    request: Request,
    method: PaymentMethod = Query(
        default=PaymentMethod.CASH,
        description="Phương thức thanh toán",
    ),
):
    order = await orderService.find(id)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn")
    if order.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    if request.state.user_role != "BusinessOwner" and order.branch.to_ref().id != PydanticObjectId(
        request.state.user_branch
    ):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    order = await orderService.update(
        id=id,
        data=OrderUpdate(
            status=OrderStatus.PAID,
            payment_method=method,
        ),
    )
    for item in order.items:
        product = await productService.find(item.get("product").id)
        item["product"] = product
    await order.fetch_all_links()
    return Response(data=order)


@apiRouter.get(
    path="/{id}/qrcode",
    name="Tạo QR Code cho đơn",
    response_model=Response,
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.order"],
            ),
        ),
    ],
)
async def gen_qr_for_order(
    id: PydanticObjectId,
    request: Request,
    template: Literal["compact2", "compact", "qr_only", "print"] = Query(
        default="compact", description="Kiểu template QR cần xuất"
    ),
):
    order = await orderService.find(id)
    if order is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn")
    if order.business.to_ref().id != PydanticObjectId(request.state.user_scope):
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    if order.branch.to_ref().id != PydanticObjectId(request.state.user_branch):
        if request.state.user_role != "BusinessOwner":
            raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    payment = await paymentService.find_one(conditions={"business.$id": order.business.to_ref().id})
    if payment is None:
        raise HTTP_404_NOT_FOUND("Yêu cầu thêm tài khoản ngân hàng")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url="https://api.vietqr.io/v2/generate",
            json={
                "accountNo": payment.accountNo,
                "accountName": payment.accountName,
                "acqId": payment.acqId,
                "amount": order.amount,
                "addInfo": f"Thanh toán đơn hàng {order.id}",
                "format": "text",
                "template": template,
            },
        )
        return Response(data=response.json())
