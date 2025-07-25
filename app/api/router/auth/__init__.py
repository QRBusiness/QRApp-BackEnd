from datetime import datetime, timedelta
from urllib.parse import urljoin

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi_mail import MessageSchema, MessageType

from app.api.dependency import login_required, role_required
from app.common.api_message import KeyResponse, get_message
from app.common.api_response import Response
from app.common.http_exception import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORZIED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from app.core.config import settings
from app.core.decorator import limiter
from app.core.security import ACCESS_JWT, REFRESH_JWT
from app.db import QRCode, SessionManager
from app.schema.business import FullBusinessResponse
from app.schema.permission import PermissionProjection
from app.schema.user import (
    Auth,
    ChangePassword,
    FullUserResponse,
    ResetPassword,
    Session,
    Token,
    UserResponse,
    UserUpdate,
)
from app.service import businessService, groupService, permissionService, userService

apiRouter = APIRouter(
    tags=["Auth"],
)


@apiRouter.post(
    path="/sign-in",
    name="Đăng nhập",
    status_code=200,
    response_model=Response[Token],
)
@limiter()
async def sign_in(data: Auth, request: Request):
    user = await userService.find_one({"username": data.username})
    if not user or not user.verify_password(data.password):
        raise HTTP_401_UNAUTHORZIED(
            error=KeyResponse.INVALID_CREDENTIALS,
            message=get_message(KeyResponse.INVALID_CREDENTIALS),
        )
    if not user.available:
        raise HTTP_403_FORBIDDEN("Tài khoản hiện bị khóa")
    if user.role in ["BusinessOwner", "Staff"]:
        business = await businessService.find(user.business.to_ref().id)
        if business.expired_at < datetime.now():
            raise HTTP_403_FORBIDDEN("Tài khoản doanh nghiệp đã hết hạn")
    # ---- #
    user_id = str(user.id)
    user_role = str(user.role)
    user_scope = str(user.business.to_ref().id) if user.business else None
    user_group = [group.to_ref().id for group in user.group] if user.group else []
    user_permissions = [permission.to_ref().id for permission in user.permissions]
    # Find Group #
    if user_group:
        # Thêm quyền của nhóm vào user_permission
        group_permissions = set()
        groups = await groupService.find_many(
            {"_id": {"$in": user_group}},
        )
        for group in groups:
            group_permissions.update(group.permissions)
        group_permissions = list(group_permissions)
        group_permissions = [permission.to_ref().id for permission in group_permissions]
        # - #
        user_permissions.extend(group_permissions)
        user_group = [str(object_id) for object_id in user_group]
    user_permissions = await permissionService.find_many(
        {"_id": {"$in": user_permissions}},
        projection_model=PermissionProjection,
    )
    user_permissions = [p.code for p in user_permissions]
    payload = {
        "user_id": user_id,
        "user_scope": user_scope,
        # "user_group": user_group, Chưa cần dùng đến group
        "user_branch": user.branch.to_dict().get("id") if user.branch else None,
        "user_role": user_role,
        "user_permissions": user_permissions,
    }
    access_token = ACCESS_JWT.encode(payload)
    refresh_token = REFRESH_JWT.encode(payload)
    SessionManager.sign_in(user_id, refresh_token)
    return Response(
        data=Token(
            access_token=access_token,
            refresh_token=SessionManager.get(user_id),
        )
    )


@apiRouter.post(
    path="/sign-out",
    name="Đăng xuất",
    status_code=200,
    dependencies=[Depends(login_required)],
    response_model=Response,
)
def sign_out(data: Session, request: Request):
    if SessionManager.get(request.state.user_id) != data.refresh_token:
        raise HTTP_403_FORBIDDEN("Đăng xuất thất bại")
    SessionManager.delete(request.state.user_id)
    if SessionManager.get(request.state.user_id):
        raise HTTP_403_FORBIDDEN("Đăng xuất thất bại")
    return Response(data="Đăng xuất thành công")


@apiRouter.post(path="/refresh-token", name="Làm mới token", response_model=Response[Token])
def refresh_token(data: Session):
    payload = REFRESH_JWT.decode(data.refresh_token)
    payload.pop("exp")
    access_token = ACCESS_JWT.encode(payload)
    return Response(data=Token(access_token=access_token, refresh_token=data.refresh_token))


@apiRouter.post(
    path="/reset-password",
    name="Lấy lại mật khẩu",
    response_model=Response[str],
)
@limiter(max_request=3, duration=600)
async def reset_password(data: ResetPassword, request: Request):
    def render_email_template(template_name: str, context: dict) -> str:
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader("app/templates"))
        template = env.get_template(template_name)
        return template.render(**context)

    account = await userService.find_one(conditions=data.model_dump())
    if account is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy tài khoản")
    # ---- #
    user_id = str(account.id)
    user_role = str(account.role)
    user_scope = str(account.business.to_ref().id) if account.business else None
    user_group = [group.to_ref().id for group in account.group] if account.group else []
    user_permissions = [permission.to_ref().id for permission in account.permissions]
    # Find Group #
    if user_group:
        # Thêm quyền của nhóm vào user_permission
        group_permissions = set()
        groups = await groupService.find_many(
            {"_id": {"$in": user_group}},
        )
        for group in groups:
            group_permissions.update(group.permissions)
        group_permissions = list(group_permissions)
        group_permissions = [permission.to_ref().id for permission in group_permissions]
        # - #
        user_permissions.extend(group_permissions)
        user_group = [str(object_id) for object_id in user_group]
    user_permissions = await permissionService.find_many(
        {"_id": {"$in": user_permissions}},
        projection_model=PermissionProjection,
    )
    user_permissions = [p.code for p in user_permissions]
    payload = {
        "user_id": user_id,
        "user_scope": user_scope,
        # "user_group": user_group, Chưa cần dùng đến group
        "user_branch": account.branch.to_dict().get("id") if account.branch else None,
        "user_role": user_role,
        "user_permissions": user_permissions,
    }
    access_token = ACCESS_JWT.encode(
        payload=payload,
        expires_delta=timedelta(minutes=15),
    )
    refresh_token = REFRESH_JWT.encode(
        payload=payload,
        expires_delta=timedelta(minutes=15),
    )
    SessionManager.sign_in(user_id, refresh_token)
    reset_url = urljoin(settings.FRONTEND_HOST, f"/reset-password?token={access_token}")
    html_body = render_email_template(
        "reset_password.html",
        {"reset_url": reset_url},
    )
    message = MessageSchema(
        subject="Reset Password",
        recipients=[data.email],
        body=html_body,
        subtype=MessageType.html,
    )
    await settings.SMTP.send_message(message)
    return Response(data="Yêu cầu đã được xử lí")


@apiRouter.post(
    path="/change-password",
    name="Đổi mật khẩu",
    dependencies=[Depends(login_required)],
    response_model=Response[UserResponse],
)
async def change_password(data: ChangePassword, request: Request):
    user = await userService.find(request.state.user_id)
    if not user.verify_password(data.old_password):
        raise HTTP_403_FORBIDDEN("Mật khẩu hiện tại không chính xác.")
    user = user.change_password(data.new_password)
    await user.save()
    return Response(data=user)


@apiRouter.get(
    path="/me",
    name="Xem thông tin cá nhân",
    status_code=200,
    response_model=Response[FullUserResponse],
    dependencies=[Depends(login_required)],
)
async def me(request: Request):
    user = await userService.find(
        request.state.user_id,
        fetch_links=True,
    )
    return Response(data=user)


@apiRouter.post(
    path="/upload-logo",
    name="Cập nhật logo doanh nghiệp",
    status_code=200,
    dependencies=[Depends(login_required), Depends(role_required(role=["BusinessOwner"]))],
    response_model=Response[bool],
)
async def upload_logo(
    request: Request,
    logo: UploadFile = File(...),
):
    if logo.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTP_400_BAD_REQUEST(message="Chỉ chấp nhận JPG, PNG, WEBP.")
    contents = await logo.read()
    if len(contents) > 2 * 1024 * 1024:  # 2MB:
        raise HTTP_400_BAD_REQUEST(message="Ảnh vượt quá 2MB")
    object_name = QRCode.upload(
        object=contents,
        object_name=f"/logo/{request.state.user_id}_{logo.filename}",
        content_type=logo.content_type,
    )
    if not await businessService.update(
        id=PydanticObjectId(request.state.user_scope), data={"logo": QRCode.get_url(object_name)}
    ):
        raise HTTP_400_BAD_REQUEST("Tải ảnh thất bại")
    return Response(data=True)


@apiRouter.post(
    path="/upload-avatar",
    name="Cập nhật ảnh đại diện",
    status_code=200,
    dependencies=[
        Depends(login_required),
    ],
    response_model=Response[UserResponse],
)
async def upload_avatar(
    request: Request,
    avatar: UploadFile = File(...),
):
    if avatar.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTP_400_BAD_REQUEST(message="Chỉ chấp nhận JPG, PNG, WEBP.")
    contents = await avatar.read()
    if len(contents) > 2 * 1024 * 1024:  # 2MB:
        raise HTTP_400_BAD_REQUEST(message="Ảnh vượt quá 2MB")
    object_name = QRCode.upload(
        object=contents,
        object_name=f"/avatar/{request.state.user_id}_{avatar.filename}",
        content_type=avatar.content_type,
    )
    user = await userService.update(
        id=request.state.user_id,
        data={
            "image_url": QRCode.get_url(object_name),
        },
    )
    await user.fetch_link("branch")
    return Response(data=user)


@apiRouter.put(
    path="/me",
    name="Sửa thông tin cá nhân",
    status_code=200,
    response_model=Response[UserResponse],
    dependencies=[
        Depends(login_required),
        Depends(
            role_required(
                role=[
                    "Admin",
                    "BusinessOwner",
                ]
            ),
        ),
    ],
)
async def put_me(data: UserUpdate, request: Request):
    user = await userService.update(id=request.state.user_id, data=data)
    return Response(data=user)


@apiRouter.get(
    path="/my-permissions",
    name="Xem quyền của cá nhân",
    status_code=200,
    response_model=Response,
    dependencies=[Depends(login_required)],
)
async def my_permission(request: Request):
    codes = request.state.user_permissions
    permissions = await permissionService.find_many({"code": {"$in": codes}})
    return Response(data=permissions)


@apiRouter.get(
    path="/my-business",
    name="Xem doanh nghiệp cá nhân",
    status_code=200,
    response_model=Response[FullBusinessResponse],
    response_model_exclude={"data": {"owner"}},
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["BusinessOwner"])),
    ],
)
async def my_business(request: Request):
    business = await businessService.find(request.state.user_scope)
    await business.fetch_all_links()
    return Response(data=business)
