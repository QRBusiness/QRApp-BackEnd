from motor.motor_asyncio import AsyncIOMotorClientSession

from app.models.user import User
from app.schema.user import UserCreate, UserUpdate
from app.service import permissionService

from .base import Service


class UserService(Service[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(User)

    async def insert(
        self,
        data,
        session: AsyncIOMotorClientSession | None = None,
    ):
        permissions = []
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        if data["role"] == "Admin":
            permissions = await permissionService.find_many(
                conditions={
                    "code": {"$regex": r"\.(businesstype|business|plan|group|user|extendorder|permission)$"},
                },
                session=session,
            )
        if data["role"] == "BusinessOwner":
            permissions = await permissionService.find_many(
                conditions={
                    "code": {
                        "$not": {"$regex": r"\.(businesstype|business|plan|permission)$"},
                    },
                },
                session=session,
            )
        if data["role"] == "Staff":
            permissions = await permissionService.find_many(
                conditions={
                    "code": {"$regex": r"^view.*(area|branch|order|category|subcategory|serviceunit|product)$"}
                },
                session=session,
            )
        data["permissions"] = permissions
        return await super().insert(data, session=session)


userService = UserService()

__all__ = ["userService"]
