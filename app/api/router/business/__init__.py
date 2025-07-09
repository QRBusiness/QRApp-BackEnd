from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Query

from app.api.dependency import (login_required, required_permissions,
                                required_role)
from app.common.api_response import Response
from app.common.http_exception import (HTTP_400_BAD_REQUEST,
                                       HTTP_404_NOT_FOUND, HTTP_409_CONFLICT)
from app.core.config import settings
from app.schema.branch import BranchCreate
from app.schema.business import (BusinessCreate, BusinessResponse,
                                 BusinessUpdate, FullBusinessResponse)
from app.schema.user import BusinessOwner, BusinessRegister, FullUserResponse
from app.service import (branchService, businessService, businessTypeService,
                         userService)

apiRouter = APIRouter(
    tags=["Business"],
    prefix="/business",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["Admin"])),
    ],
)


@apiRouter.get(
    path="",
    name="Danh sách doanh nghiệp",
    status_code=200,
    dependencies=[Depends(required_permissions(permissions=["view.business"]))],
    response_model=Response[List[BusinessResponse]],
)
async def get_businesses(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
    type: str = Query(default=None, description="Lọc theo loại doanh nghiệp"),
    available: Optional[bool] = Query(default=None),
):
    conditions = {}
    if available is not None:
        conditions["available"] = available
    if type:
        types = await businessTypeService.find_many(
            {"name": {"$regex": type, "$options": "i"}}
        )
        type_ids = [type.id for type in types]
        conditions["business_type._id"] = {"$in": type_ids}
    businesses = await businessService.find_many(
        conditions, skip=(page - 1) * limit, limit=limit, fetch_links=True
    )
    return Response(data=businesses)


@apiRouter.get(
    path="/{id}",
    name="Xem doanh nghiệp",
    status_code=200,
    dependencies=[Depends(required_permissions(permissions=["view.business"]))],
    response_model=Response[FullBusinessResponse],
)
async def get_business(id: PydanticObjectId):
    business = await businessService.find(id)
    if business is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    await business.fetch_all_links()
    return Response(data=business)


@apiRouter.put(
    path="/{id}",
    name="Sửa thông tin doanh nghiệp",
    status_code=200,
    dependencies=[Depends(required_permissions(permissions=["update.business"]))],
    response_model=Response[FullBusinessResponse],
)
async def put_business(id: PydanticObjectId, data: BusinessUpdate):
    business = await businessService.find(id)
    if business is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if business := await businessService.find_one({"contact": data.contact}):
        if business.id != id:
            raise HTTP_409_CONFLICT("Liên hệ được doanh nghiệp khác sử dụng")
    business = await businessService.update(id, data)
    await business.fetch_all_links()
    return Response(data=business)


@apiRouter.post(
    path="",
    name="Đăng kí doanh nghiệp",
    status_code=201,
    dependencies=[Depends(required_permissions(permissions=["create.business"]))],
    response_model=Response[FullUserResponse],
)
async def post_business(data: BusinessRegister):
    type = await businessTypeService.find(data.business_type)
    if type is None:
        raise HTTP_400_BAD_REQUEST("Loại doanh nghiệp không phù hợp")
    if await businessService.find_one({"name": data.business_name}):
        raise HTTP_409_CONFLICT("Tên doanh nghiệp đã được đăng kí")
    if await userService.find_one(
        {"username": data.username},
    ):
        raise HTTP_409_CONFLICT("Tên người dùng đã được đăng kí")
    if await userService.find_one({"phone": data.owner_contact}):
        raise HTTP_409_CONFLICT("Số điện thoại người khác đã được sử dụng")
    if data.business_tax_code:
        if await businessService.find_one({"tax_code": data.business_tax_code}):
            raise HTTP_409_CONFLICT("Mã số thuế đã được sử dụng")
    business = BusinessCreate(
        name=data.business_name,
        address=data.business_address,
        contact=data.business_contact,
        business_type=type,
        tax_code=data.business_tax_code,
        owner=None,
    )
    owner = BusinessOwner(
        username=data.username,
        password=data.password,
        name=data.owner_name,
        phone=data.owner_contact,
        address=data.owner_address,
    )
    business = await businessService.insert(business)
    owner = await userService.insert(owner)
    business = await businessService.update(
        id=business.id,
        data={
            "owner": owner,
        },
    )
    await userService.update(
        id=owner.id,
        data={
            "business": business,
        },
    )
    await branchService.insert(
        BranchCreate(
            name=business.name,
            address=business.address,
            contact=business.contact,
            business=business,
        )
    )
    user = await userService.find_one({"username": data.username})
    await user.fetch_all_links()
    return Response(data=user)


@apiRouter.put(
    path="/active/{id}",
    name="Mở/Khóa doanh nghiệp",
    dependencies=[Depends(required_permissions(permissions=["update.business"]))],
    response_model=Response[BusinessResponse],
)
async def lock_unlock_business(id: PydanticObjectId):
    business = await businessService.find(id)
    if business is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy doanh nghiệp")
    business = await businessService.update(
        id=id, data={"available": not business.available}
    )
    owner_id = business.owner.to_ref().id
    await userService.update(id=owner_id, data={"available": business.available})
    await business.fetch_link("business_type")
    return Response(data=business)
