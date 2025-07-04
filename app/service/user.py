from app.models.user import User
from app.schema.user import UserCreate, UserUpdate
from app.service import permissionService

from .base import Service


class UserService(Service[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def insert(self, data):
        permissions = []
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        if data["role"] == "Admin":
            permissions = await permissionService.find_many()
        if data["role"] == "BusinessOwner":
            permissions = await permissionService.find_many({})
            permissions = [
                permission
                for permission in permissions
                if not permission.code.endswith((".businesstype", ".business"))
            ]
        data["permissions"] = permissions
        return await super().insert(data)


userService = UserService()

__all__ = ["userService"]
