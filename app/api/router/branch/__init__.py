from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request

from app.api.dependency import (login_required, required_permissions,
                                required_role)
from app.common.api_response import Response
from app.common.http_exception import (HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
                                       HTTP_409_CONFLICT)
from app.db import Mongo
from app.schema.branch import (BranchCreateWithoutBusiness, BranchResponse,
                               BranchUpdate)
from app.service import branchService, businessService, userService

apiRouter = APIRouter(
    tags=["Branch"],
    prefix="/branches",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["BusinessOwner","Staff"])),
    ],
)


@apiRouter.get(
    path="",
    status_code=200,
    name="Danh sách chi nhánh (Thuộc quyền sở hữu)",
    response_model=Response[List[BranchResponse]],
    dependencies=[
        Depends(required_permissions(permissions=['view.branch']))
    ]
)
async def get_branchs(request: Request):
    business_id = request.state.user_scope
    branches = await branchService.find_many(
        conditions={"business.$id": PydanticObjectId(business_id)}
    )
    return Response(data=branches)


@apiRouter.post(
    path="",
    status_code=201,
    name="Thêm chi nhánh cho doanh nghiệp",
    response_model=Response[BranchResponse],
    dependencies=[
        Depends(required_permissions(permissions=['create.branch']))
    ]
)
async def post_branch(data: BranchCreateWithoutBusiness, request: Request):
    business = await businessService.find(request.state.user_scope)
    if branch := await branchService.find_one(
        conditions={
            "business.$id": business.id,
            "name": data.name,
        }
    ):
        raise HTTP_409_CONFLICT(f"Chi nhánh {data.name} đã tồn tại")
    if data.contact is None:
        data.contact = business.contact
    data = data.model_dump()
    data["business"] = business
    branch = await branchService.insert(data)
    return Response(data=branch)


@apiRouter.put(
    path="/{id}",
    status_code=200,
    name="Sửa thông tin chi nhánh",
    response_model=Response[BranchResponse],
    dependencies=[
        Depends(required_permissions(permissions=['update.branch']))
    ]
)
async def update_branch(id: PydanticObjectId, data: BranchUpdate, request: Request):
    branch = await branchService.find(id)
    if branch is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    branch_scope = branch.business.to_ref().id
    user_scope = PydanticObjectId(request.state.user_scope)
    if branch_scope != user_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    branch = await branchService.update(id=id, data=data.model_dump(exclude_none=True))
    return Response(data=branch)


@apiRouter.delete(
    path="/{id}", 
    name="Xóa chi nhánh", 
    response_model=Response,
    dependencies=[
        Depends(required_permissions(permissions=['delete.branch']))
    ]
)
async def delete_branch(id: PydanticObjectId, request: Request):
    async with businessService.transaction(Mongo.client) as session:
        branch = await branchService.find(id,session=session)
        if branch is None:
            raise HTTP_404_NOT_FOUND("Không tìm thấy chi nhánh")
        branch_scope = branch.business.to_ref().id
        user_scope = PydanticObjectId(request.state.user_scope)
        if branch_scope != user_scope:
            raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
        await branchService.delete(id,session=session)
        await userService.delete_many(conditions={
            "branch.$id":id
        })
        return Response(data="Xóa thành công")
