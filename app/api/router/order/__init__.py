from datetime import datetime, timedelta
from typing import List, Literal, Optional

import httpx
from beanie import Link, PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request
from jwt.exceptions import ExpiredSignatureError

from app.api.dependency import login_required, permission_required, role_required
from app.common.api_response import Response
from app.common.http_exception import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from app.core.config import settings
from app.core.security import ACCESS_JWT
from app.db import Mongo
from app.schema.area import AreaResponse
from app.schema.branch import BranchResponse
from app.schema.order import (
    CheckoutOrder,
    MinimumOrderResponse,
    OrderResponse,
    OrderStatus,
    OrderUpdate,
    PaymentMethod,
    Report,
)
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
    path="/report",
    response_model=Response[Report],
    name="Thống kê doanh số",
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.order"],
            ),
        ),
    ],
)
async def report(
    request: Request,
    branch: Optional[PydanticObjectId] = Query(default=None),
    area: Optional[PydanticObjectId] = Query(default=None),
    service_unit: Optional[PydanticObjectId] = Query(default=None),
    product: Optional[PydanticObjectId] = Query(default=None),
    staff: Optional[PydanticObjectId] = Query(default=None),
    method: Optional[PaymentMethod] = Query(default=None),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
):
    if request.state.user_role != "BusinessOwner":
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    conditions = {
        "business._id": PydanticObjectId(request.state.user_scope),
        "status": OrderStatus.PAID,
    }
    if branch:
        conditions["branch._id"] = branch
    if area:
        conditions["area._id"] = area
    if service_unit:
        conditions["service_unit._id"] = service_unit
    if method:
        conditions["payment_method"] = method
    if staff:
        conditions["staff"] = staff
    if product:
        conditions["items.product.$id"] = product
    if start_date and end_date:
        conditions["created_at"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        conditions["created_at"] = {"$gte": start_date}
    elif end_date:
        conditions["created_at"] = {"$lte": end_date}
    orders = await orderService.find_many(
        conditions,
        fetch_links=True,
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
    return Response(
        data=Report(
            orders=orders,
            total_amount=sum([order.amount for order in orders]),
            total_count=len(orders),
        ),
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
    path="/checkout",
    name="Thông tin đơn hàng",
    response_model=Response[CheckoutOrder],
    dependencies=[
        Depends(
            permission_required(
                permissions=["update.order"],
            ),
        ),
    ],
)
async def view_checkout(
    request: Request,
    token: str = Query(...),
    template: Literal["compact2", "compact", "qr_only", "print"] = Query(
        default="compact", description="Kiểu template QR cần xuất"
    ),
):
    try:
        payload = ACCESS_JWT.decode(token)
        if request.state.user_scope != payload.get("business"):
            raise HTTP_404_NOT_FOUND("Không tìm thấy đơn hàng")
        orders = [PydanticObjectId(order) for order in payload.get("orders")]
        orders = await orderService.find_many(
            conditions={"_id": {"$in": orders}},
            projection_model=MinimumOrderResponse,
        )
        for order in orders:
            for item in order.items:
                item["product"] = str(item["product"].id)
        payment = await paymentService.find_one(
            conditions={
                "business.$id": PydanticObjectId(request.state.user_scope),
            },
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url="https://api.vietqr.io/v2/generate",
                json={
                    "accountNo": payment.accountNo,
                    "accountName": payment.accountName,
                    "acqId": payment.acqId,
                    "amount": order.amount,
                    "addInfo": "Thanh toán đơn hàng",
                    "format": "text",
                    "template": template,
                },
            )
            qr_code = response.json().get("data").get("qrDataURL")
        data = CheckoutOrder(
            qr_code=qr_code,
            orders=orders,
        )
        return Response(data=data)
    except ExpiredSignatureError as e:
        raise HTTP_400_BAD_REQUEST("Liên kết thanh toán đã hết hạn. Vui lòng tạo lại phiên thanh toán mới.") from e


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
    path="/checkout",
    name="Xác nhận đơn hàng",
    response_model=Response[str],
    dependencies=[
        Depends(
            permission_required(
                permissions=["update.order"],
            ),
        ),
    ],
)
async def post_orders(
    request: Request,
    token: str = Query(...),
    method: PaymentMethod = Query(
        default=PaymentMethod.CASH,
        description="Phương thức thanh toán",
    ),
):
    try:
        payload = ACCESS_JWT.decode(token)
        if request.state.user_scope != payload.get("business"):
            raise HTTP_404_NOT_FOUND("Không tìm thấy đơn hàng")
        async with orderService.transaction(Mongo.client) as session:
            for oid in payload.get("orders"):
                await orderService.update(
                    id=PydanticObjectId(oid),
                    data=OrderUpdate(
                        status=OrderStatus.PAID,
                        payment_method=method,
                    ),
                    session=session,
                )
        return Response(data="Đơn hàng đã được xử lí")
    except ExpiredSignatureError as e:
        raise HTTP_400_BAD_REQUEST("Liên kết thanh toán đã hết hạn. Vui lòng tạo lại phiên thanh toán mới.") from e


@apiRouter.post(
    path="/qrcode",
    name="Tổng hợp thông tin đơn hàng",
    response_model=Response[str],
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.order"],
            ),
        ),
    ],
)
async def gen_qr_for_orders(
    request: Request,
    orders: List[PydanticObjectId],
):
    orders = await orderService.find_many(
        conditions={
            "_id": {"$in": orders},
            "business.$id": PydanticObjectId(request.state.user_scope),
            "status": OrderStatus.UNPAID,
        }
    )
    if not orders:
        raise HTTP_404_NOT_FOUND("Không tìm thấy đơn hàng")
    payload = {
        "orders": [str(order.id) for order in orders],
        "business": request.state.user_scope,
        "branch": request.state.user_branch,
        "action": "checkout",
    }
    token = ACCESS_JWT.encode(
        payload=payload,
        expires_delta=timedelta(minutes=60),
    )
    return Response(data=token)
