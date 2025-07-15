from typing import List, Literal, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request

from app.api.dependency import login_required, required_permissions, required_role
from app.common.api_message import KeyResponse, get_message
from app.common.api_response import Response
from app.common.http_exception import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.db import SessionManager
from app.schema.user import FullUserResponse, Staff, UserResponse, UserUpdate
from app.service import branchService, businessService, permissionService, userService

apiRouter = APIRouter(
    tags=["User"],
    prefix="/users",
    dependencies=[
        Depends(login_required),
        Depends(required_role(role=["Admin", "BusinessOwner"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem danh sách",
    response_model=Response[List[UserResponse]],
    dependencies=[
        Depends(
            required_permissions(
                permissions=["view.user"],
            ),
        ),
    ],
)
async def get_users(
    request: Request,
    role: Optional[Literal["Admin", "BusinessOwner", "Staff"]] = Query(default=None, description="Lọc theo vai trò"),
):
    user_scope = request.state.user_scope
    if user_scope is None:
        conditions = {}
        if role:
            conditions["role"] = role
        users = await userService.find_many(conditions, projection_model=UserResponse, fetch_links=True)
    else:
        users = await userService.find_many(
            {
                "business._id": PydanticObjectId(user_scope),
                "role": "Staff",
            },
            projection_model=UserResponse,
            fetch_links=True,
        )
    return Response(data=users)


@apiRouter.get(
    path="/{id}",
    name="Xem chi tiết",
    response_model=Response[FullUserResponse],
    dependencies=[Depends(required_permissions(permissions=["view.user"]))],
)
async def get_user(id: PydanticObjectId, request: Request):
    staff = await userService.find(id)
    if staff is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    user_scope = request.state.user_scope
    staff_scope = str(staff.business.to_ref().id)
    if user_scope is not None and user_scope != staff_scope:
        raise HTTP_403_FORBIDDEN("Bạn không đủ quyền thực hiện hành động này")
    await staff.fetch_all_links()
    return Response(data=staff)


@apiRouter.post(
    path="",
    name="Tạo người dùng/nhân viên",
    response_model=Response[UserResponse],
    dependencies=[Depends(required_permissions(permissions=["create.user"]))],
)
async def post_user(data: Staff, request: Request):
    branch = await branchService.find(data.branch)
    if branch is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy chi nhánh")
    if str(branch.business.to_ref().id) != request.state.user_scope:
        raise HTTP_403_FORBIDDEN("Chi nhánh không tồn tại trong doanh nghiệp của bạn")
    data = data.model_dump()
    user_scope = request.state.user_scope
    business = await businessService.find(user_scope)
    data["business"] = business
    data["branch"] = branch
    staff = await userService.insert(data)
    return Response(data=staff)


@apiRouter.post(
    path="/permission/{id}",
    name="Cấp quyền cho nhân viên",
    response_model=Response[FullUserResponse],
    response_model_exclude={"data": {"group", "business"}},
)
async def post_permission(id: PydanticObjectId, permissions: List[PydanticObjectId], request: Request):
    staff = await userService.find_one(
        conditions={
            "_id": id,  # Tìm theo id
            "role": "Staff",  # Là nhân viên của doanh nghiệp
            "business.$id": PydanticObjectId(request.state.user_scope),
        }
    )
    if staff is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy nhân viên trong doanh nghiệp của bạn")
    permissions = await permissionService.find_many(
        conditions={
            "_id": {"$in": permissions},
        }
    )
    staff = await userService.update(
        id=staff.id,
        data={"permissions": permissions},  # [perm.to_ref() for perm in permissions]
    )
    await staff.fetch_all_links()
    return Response(data=staff)


@apiRouter.delete(
    path="/permission/{id}",
    name="Thu hồi nhân viên",
    response_model=Response[FullUserResponse],
    response_model_exclude={"data": {"group", "business"}},
)
async def delete_permission(id: PydanticObjectId, permissions: List[PydanticObjectId], request: Request):
    staff = await userService.find_one(
        conditions={
            "_id": id,  # Tìm theo id
            "role": "Staff",  # Là nhân viên của doanh nghiệp
            "business.$id": PydanticObjectId(request.state.user_scope),
        }
    )
    if staff is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy nhân viên trong doanh nghiệp của bạn")
    permissions = await permissionService.find_many(
        conditions={
            "_id": {"$in": permissions},
        }
    )
    staff = await userService.update_one(
        id=staff.id,
        conditions={"$pull": {"permissions": {"$in": [p.id for p in permissions]}}},
    )
    await staff.fetch_all_links()
    return Response(data=staff)


@apiRouter.put(
    path="/{id}",
    name="Sửa thông tin nhân viên/người dùng",
    response_model=Response[UserResponse],
)
async def put_user(id: PydanticObjectId, data: UserUpdate, request: Request):
    if request.state.user_role != "Admin":
        user = await userService.find_one(
            {
                "_id": id,
                "role": "Staff",
            }
        )
        if user is None or user.business.to_ref().id != PydanticObjectId(request.state.user_scope):
            raise HTTP_404_NOT_FOUND("Không tìm thấy người dùng trong doanh nghiệp của bạn")
    else:
        user = await userService.find_one(
            {"_id": id},
        )
        if user is None:
            raise HTTP_404_NOT_FOUND("Không tìm thấy người dùng trong doanh nghiệp của bạn")
    if user := await userService.find_one(
        {"phone": data.phone},
    ):
        if user.id != id:
            raise HTTP_409_CONFLICT("Số điện thoại đã được đăng kí")
    user = await userService.update(id, data)
    await user.fetch_all_links()
    return Response(data=user)


@apiRouter.put(
    path="/active/{id}",
    name="Mở/Khóa người dùng/nhân viên",
    response_model=Response[UserResponse],
    dependencies=[
        Depends(
            required_permissions(
                permissions=[
                    "update.user",
                ],
            ),
        ),
    ],
)
async def lock_unlock_user(id: PydanticObjectId, request: Request, task: BackgroundTasks):
    def remove_session(user_id: str):
        SessionManager.delete(user_id)

    user = await userService.find(id)
    if user is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    user_request_scope = request.state.user_scope
    if user_request_scope is None or user_request_scope == str(user.business.to_ref().id):
        user = await userService.update(id=id, data={"available": not user.available})
        task.add_task(remove_session, str(id))
        return Response(data=user)
    raise HTTP_403_FORBIDDEN(get_message(KeyResponse.PERMISSION_DENIED))
