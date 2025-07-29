from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query, Request

from app.api.dependency import login_required, role_required
from app.api.router.area import apiRouter as areaRouter
from app.api.router.auth import apiRouter as authRouter
from app.api.router.branch import apiRouter as branchRouter
from app.api.router.business import apiRouter as businessRouter
from app.api.router.business_type import apiRouter as businesstypeRouter
from app.api.router.category import apiRouter as categoryRouter
from app.api.router.group import apiRouter as groupRouter
from app.api.router.order import apiRouter as orderRouter
from app.api.router.payment import apiRouter as paymentRouter
from app.api.router.permission import apiRouter as permissionRouter
from app.api.router.plan import apiRouter as planRouter
from app.api.router.product import private_apiRouter as private_productRouter
from app.api.router.product import public_apiRouter as public_productRouter
from app.api.router.request import apiRouter as requestRouter
from app.api.router.service_unit import apiRouter as serviceRouter
from app.api.router.user import apiRouter as userRouter
from app.common.api_response import Response
from app.common.http_exception import HTTP_404_NOT_FOUND
from app.socket import manager

api = APIRouter()
api.include_router(authRouter)
api.include_router(permissionRouter)
api.include_router(businesstypeRouter)
api.include_router(planRouter)
api.include_router(businessRouter)
api.include_router(branchRouter)
api.include_router(paymentRouter)
api.include_router(groupRouter)
api.include_router(userRouter)
api.include_router(areaRouter)
api.include_router(serviceRouter)
api.include_router(categoryRouter)
api.include_router(public_productRouter)
api.include_router(private_productRouter)
api.include_router(requestRouter)
api.include_router(orderRouter)


# broadcast message
@api.post(
    path="/broadcast",
    tags=["WebSocket"],
    name="Broadcast message",
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["Admin"])),
    ],
    response_model=Response[bool],
)
async def broadcast_message(
    users: Optional[List[PydanticObjectId]] = Query(
        default=None,
        description="🔸 Danh sách `user_id` cần gửi tin nhắn trực tiếp",
    ),
    group: Optional[str] = Query(
        default=None,
        description=(
            "🏢 Tên nhóm chính để gửi tin nhắn:\n"
            "- `System`: Dành cho người quản trị không thuộc doanh nghiệp\n"
            "- `<business_id>`: ID của doanh nghiệp (dành cho nhân viên doanh nghiệp)"
        ),
    ),
    branch: Optional[str] = Query(
        default=None,
        description="🏬 Mã chi nhánh (`branch_id`) thuộc `group` đã chỉ định (doanh nghiệp hoặc System).",
    ),
    permission: Optional[str] = Query(default=None, description="👤 Quyền hạn người dùng trong chi nhánh."),
    message: str = Query(
        ...,
        description="🔊 Nội dung tin nhắn sẽ được gửi tới người dùng thông qua WebSocket.",
    ),
):
    await manager.broadcast(
        message=message,
        user_ids=users,
        business=group,
        branch=branch,
        permission=permission,
    )
    return Response(data=True)


# Webhook
@api.post(
    tags=["Webhook"],
    path="/webhook",
    status_code=200,
    name="Webhook",
    response_model=Response,
)
def receive_webhook():
    return Response(data=True)


# Health check
@api.get(
    tags=["Health check"],
    path="/health-check",
    status_code=200,
    name="Health Check",
    response_model=Response,
)
def health_check():
    return Response(data=True)


# Handle Undefined API
@api.api_route(
    tags=["Proxy"],
    path="/{path:path}",
    methods=["GET", "POST"],
    include_in_schema=False,
)
async def catch_all(path: str, request: Request):
    raise HTTP_404_NOT_FOUND(error="NOT FOUND", message=f"{request.method} {request.url.path} is undefined")
