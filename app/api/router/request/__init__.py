import json
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.api.dependency import login_required, required_role
from app.common.api_response import Response
from app.common.http_exception import (HTTP_400_BAD_REQUEST,
                                       HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND)
from app.core.config import settings
from app.core.decorator import limiter
from app.db import QRCode
from app.models.request import RequestType
from app.schema.order import ExtenOrderCreate
from app.schema.request import (MinimumResquestResponse, RequestCreate,
                                RequestStatus, RequestUpdate, ResquestResponse)
from app.service import (areaService, businessService, extendOrderService,
                         planService, productService, requestService,
                         unitService, userService)
from app.socket import manager

apiRouter = APIRouter(
    tags = ['Request'],
    prefix = "/request"
)

@apiRouter.get(
    path = "/extend",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["Admin"]))
    ],
    response_model=Response
)
async def get_extends():
    orders = await extendOrderService.find_many(conditions={})
    return Response(data=orders)

@apiRouter.post(
    path = "/extend",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["BusinessOwner"]))
    ],
    response_model=Response[str]
)
async def request_extend(
    request:Request,
    plan: PydanticObjectId = Form(...,description="Gói đăng kí"),
    image: UploadFile = File(..., description="Ảnh minh chứng gia hạn"),
):
    plan = await planService.find(plan)
    if plan is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy gói đăng kí")
    business = await businessService.find(request.state.user_scope)
    contents = await image.read()
    object_name = QRCode.upload(
        object=contents,
        object_name=f"/transaction/{request.state.user_id}_{image.filename}",
        content_type=image.content_type,
    )
    await extendOrderService.insert(ExtenOrderCreate(
        business = business,
        plan=plan,
        image=QRCode.get_url(object_name)
    ))
    return Response(data="Yêu cầu đã được xử lí")

@apiRouter.get(
    path = "",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["BusinessOwner","Staff"]))
    ],
    response_model=Response[List[ResquestResponse]]
)
@limiter(max_request=10)
async def get_requests(
    request:Request,
    status: Optional[RequestStatus] = Query(default=None,description="Lọc theo trạng thái"),
    type: Optional[RequestType] = Query(default=None,description="Lọc theo type"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    conditions={
        "business._id":PydanticObjectId(request.state.user_scope)
    }
    if request.state.user_branch:
        conditions["branch._id"] = PydanticObjectId(request.state.user_branch)
    if status:
        conditions['status'] = status.value
    if type:
        conditions['type'] = type
    requests = await requestService.find_many(
        conditions=conditions,
        projection_model=ResquestResponse,
        fetch_links=True,
        skip=(page - 1) * limit, 
        limit=limit
    )
    return Response(data=requests)

@apiRouter.post(
    path = "",
    response_model = Response[MinimumResquestResponse]
)
@limiter(max_request=10)
async def request(data:RequestCreate,request:Request):
    service_unit = await unitService.find_one(conditions={
        "_id":data.service_unit,
        "area.$id":data.area
    }) 
    if service_unit is None:
        raise HTTP_400_BAD_REQUEST("Yêu cầu không phù hợp")
    area = await areaService.find(service_unit.area.to_ref().id)
    data = data.model_dump()
    data['branch'] = area.branch.to_ref()
    data['business'] = area.business.to_ref()
    if data.get("type") == RequestType.ORDER:
        # -- Check valid order
        product_ids = [PydanticObjectId(e.get("_id")) for e in data.get("data")]
        products = await productService.find_many(conditions={
            "_id": {"$in": product_ids}
        })
        if len(products) != len(data.get("data")):
            raise HTTP_400_BAD_REQUEST("Kiểm tra thông tin đơn hàng")
        product_map = {str(product.id): product for product in products}
        for p in data.get("data"):
            db_product = product_map.get(p.get("_id"))
            if p.get("variant") not in [option.type for option in db_product.variants]:
                raise HTTP_400_BAD_REQUEST("Kiểm tra thông tin đơn hàng")
            if any(opt not in [option.type for option in db_product.options] for opt in p.get("options", [])):
                raise HTTP_400_BAD_REQUEST("Kiểm tra thông tin đơn hàng")
    req = await requestService.insert(data)
    await manager.broadcast(
        message=json.dumps({
            "message":f"{data.get("type")} {data.get("reason")}",
            "request": str(req.id),
            "data":data.get("data"),
        }),
        business=area.business.to_dict().get("id"),
        branch=area.branch.to_dict().get("id"),
        permission="receive.request",
    )
    return Response(data=req)

@apiRouter.post(
    path = "/process/{id}",
    response_model = Response,
    dependencies=[
        Depends(login_required)
    ]
)
async def process_request(id:PydanticObjectId,req:Request):
    request = await requestService.find(id)
    if request is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy yêu cầu")
    if req.state.user_scope != request.business.to_dict().get("id") or request.branch.to_dict().get("id") != req.state.user_branch:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    user = await userService.find(req.state.user_id)
    if request.status == RequestStatus.COMPLETED or (request.status != RequestStatus.WAITING and request.staff.to_dict().get("id") != str(user.id)):
        await manager.broadcast(message="Yêu cầu đã được xử lí", user_ids=[PydanticObjectId(req.state.user_id)])
        return Response(data=False)
    await requestService.update(id,RequestUpdate(
            status = request.status.next(),
            staff = user.to_ref()
        ))
    return Response(data=True)