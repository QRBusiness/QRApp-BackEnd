from beanie import PydanticObjectId
from fastapi import APIRouter, Depends

from app.api.dependency import login_required, role_required
from app.common.api_response import Response
from app.common.http_exception import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.schema.plan import PlanCreate, PlanResponse, PlanUpdate
from app.service import paymentService, planService

apiRouter = APIRouter(
    tags=["Plan"],
    prefix="/plan",
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["Admin"])),
    ],
)


@apiRouter.post(
    path="",
    response_model=Response[PlanResponse],
    response_model_exclude={"data": "qr_code"},
    name="Thêm gói gia hạn",
)
async def post_plan(data: PlanCreate):
    payment = await paymentService.find_one(conditions={"business.$id": None})
    if payment is None:
        raise HTTP_400_BAD_REQUEST("Không tìm thấy thông tin thanh toán")
    if await planService.find_one({"$or": [{"name": data.name}, {"period": data.period}]}):
        raise HTTP_409_CONFLICT("Gói đã tồn tại")
    plan = await planService.insert(data)
    return Response(data=plan)


@apiRouter.put(
    path="/{id}",
    response_model=Response[PlanResponse],
    name="Chỉnh sửa gói gia hạn",
)
async def put_plan(id: PydanticObjectId, data: PlanUpdate):
    plan = await planService.find(id)
    if plan is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy gói")
    if await planService.find_one(
        {"$and": [{"_id": {"$ne": id}}, {"$or": [{"name": data.name}, {"period": data.period}]}]}
    ):  # loại trừ chính nó
        raise HTTP_409_CONFLICT("Gói đã tồn tại")
    plan = await planService.update(id, data)
    return Response(data=plan)


@apiRouter.delete(path="/{id}", response_model=Response[bool], name="Xóa gói gia hạn")
async def delete_plan(id: PydanticObjectId):
    plan = await planService.find(id)
    if plan is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if await planService.delete(id):
        return Response(data=True)
    return Response(data=False)
