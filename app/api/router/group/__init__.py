from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, Request
from fastapi.encoders import jsonable_encoder

from app.api.dependency import login_required, required_permissions, required_role
from app.common.api_message import KeyResponse, get_message
from app.common.api_response import Response
from app.common.http_exception import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.db import Mongo
from app.schema.group import FullGroupResponse, GroupCreate, GroupResponse
from app.service import businessService, groupService, permissionService, userService

apiRouter = APIRouter(
    tags=["Group"],
    prefix="/groups",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["Admin", "BusinessOwner"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem danh sách nhóm (Thuộc quyền sở hữu)",
    response_model=Response[List[GroupResponse]],
)
async def get_groups(request: Request):
    groups = await groupService.find_many(
        {"business._id": PydanticObjectId(request.state.user_scope)}, fetch_links=True
    )
    return Response(data=groups)


@apiRouter.get(
    path="/{id}",
    name="Xem chi tiết nhóm (Thuộc quyền sở hữu)",
    response_model=Response,
    response_model_exclude={"data": "business"},
)
async def get_group(id: PydanticObjectId, request: Request):
    group = await groupService.find(id)
    if PydanticObjectId(request.state.user_scope) == group.business.to_ref().id:
        await group.fetch_link("permissions")
        data = await FullGroupResponse.from_model(group)
        data.users = jsonable_encoder(data.users)
        return Response(data=data)
    raise HTTP_403_FORBIDDEN(get_message(KeyResponse.PERMISSION_DENIED))


@apiRouter.post(
    path="",
    name="Tạo nhóm",
    response_model=Response[GroupResponse],
    dependencies=[
        Depends(required_permissions(permissions=["create.group"])),
    ],
)
async def post_group(data: GroupCreate, request: Request):
    data = data.model_dump()
    business = await businessService.find(request.state.user_scope)
    data["business"] = business
    group_in_business = await groupService.find_many({"business.$id": PydanticObjectId(request.state.user_scope)})
    if any(group.name.lower() == data["name"].lower() for group in group_in_business):
        raise HTTP_409_CONFLICT(f"Đã có nhóm {data["name"]} tại doanh nghiệp này")
    group = await groupService.insert(data)
    return Response(data=group)


@apiRouter.delete(
    path="/{id}",
    name="Xóa nhóm",
    dependencies=[
        Depends(
            required_permissions(
                permissions=[
                    "delete.group",
                ],
            ),
        ),
    ],
    response_model=Response[str],
)
async def delete_group(id: PydanticObjectId, request: Request):
    async with groupService.transaction(Mongo.client) as session:
        if (
            await groupService.find_one(
                conditions={
                    "_id": id,
                    "business.$id": PydanticObjectId(request.state.user_scope),
                },
                session=session,
            )
            is None
        ):
            raise HTTP_404_NOT_FOUND("Không tìm thấy nhóm")
        await groupService.delete(
            id,
            session=session,
        )
        await userService.update_many(
            conditions={
                "group.$id": id,
            },
            update_data={
                "$pull": {
                    "group": {"$id": id},
                },
            },
            session=session,
        )
    return Response(data="Xóa thành công")


@apiRouter.post(
    path="/{id}/permissions",
    name="Cấp quyền",
    response_model=Response[GroupResponse],
)
async def give_permissions(
    id: PydanticObjectId,
    request: Request,
    data: List[PydanticObjectId] | None = None,
):
    # Check scope
    group = await groupService.find(id)
    if group is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    user = await userService.find(request.state.user_id)
    if user.business.to_ref().id != group.business.to_ref().id:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    # Grant permission
    data = data or []
    grant_permissions = await permissionService.find_many(
        conditions={
            "_id": {
                "$in": data,
            }
        },
    )
    grant_permission_ids = [p.id for p in grant_permissions]
    # User permission
    user_permissions = [permission.to_ref().id for permission in user.permissions]
    # Check
    if any(permission not in user_permissions for permission in grant_permission_ids):
        raise HTTP_403_FORBIDDEN("Cần có quyền để cấp")
    group = await groupService.update(id=id, data={"permissions": grant_permissions})
    await group.fetch_link("permissions")
    return Response(data=group)


@apiRouter.delete(
    path="/{id}/permissions",
    name="Thu hồi quyền",
    response_model=Response[GroupResponse],
)
async def delete_permissions(id: PydanticObjectId, request: Request, data: List[PydanticObjectId] | None = None):
    # Check scope
    group = await groupService.find(id)
    if group is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    user = await userService.find(request.state.user_id)
    if user.business.to_ref().id != group.business.to_ref().id:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    # Grant permission
    data = data or []
    grant_permissions = await permissionService.find_many(
        conditions={
            "_id": {"$in": data},
        },
    )
    if not grant_permissions:
        await group.fetch_link("permissions")
        return Response(data=group)
    group = await groupService.update_one(
        id=id,
        conditions={
            "$pull": {
                "permissions": {
                    "$in": [p.to_ref() for p in grant_permissions],
                },
            },
        },
    )
    await group.fetch_link("permissions")
    return Response(data=group)


@apiRouter.post(
    path="/{id}/user/{user_id}",
    name="Thêm nhân viên vào nhóm",
    status_code=200,
    response_model=Response[bool],
)
async def add_to_group(id: PydanticObjectId, user_id: PydanticObjectId | str, request: Request):
    group = await groupService.find(id)
    if group is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy nhóm")
    group_scope = group.business.to_ref().id
    current_scope = PydanticObjectId(request.state.user_scope)
    if current_scope != group_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    conditions = {"$or": [{"_id": user_id}, {"username": user_id}]}
    if not PydanticObjectId.is_valid(user_id):
        conditions["$or"] = conditions.get("$or")[1:]
    user = await userService.find_one(conditions)
    if user is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy người dùng")
    user_scope = user.business.to_ref().id
    if current_scope != user_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    await userService.update_one(id=user.id, conditions={"$addToSet": {"group": group.to_ref()}})
    return Response(data=True)


@apiRouter.delete(
    path="/{id}/user/{user_id}",
    name="Xóa nhân viên trong nhóm",
)
async def delete_to_group(id: PydanticObjectId, user_id: PydanticObjectId | str, request: Request):
    group = await groupService.find(id)
    if group is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy nhóm")
    group_scope = group.business.to_ref().id
    current_scope = PydanticObjectId(request.state.user_scope)
    if current_scope != group_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    conditions = {
        "$or": [
            {"_id": user_id},
            {"username": user_id},
        ],
    }
    if not PydanticObjectId.is_valid(user_id):
        conditions["$or"] = conditions.get("$or")[1:]
    user = await userService.find_one(conditions)
    if user is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy người dùng")
    user_scope = user.business.to_ref().id
    if current_scope != user_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    await userService.update_one(
        id=user.id,
        conditions={"$pull": {"group": group.to_ref()}},
    )
    return Response(data=True)
