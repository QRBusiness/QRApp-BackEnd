from typing import List, Optional

from pydantic import BaseModel, Field

from app.schema import BaseResponse
from app.schema.permission import DetailPermissionResponse


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = Field(default=None, description="Optional description")


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupResponse(BaseResponse):
    name: str
    description: Optional[str] = None
    permissions: List[DetailPermissionResponse] = []


class FullGroupResponse(GroupResponse):
    users: Optional[List[BaseModel]] = []

    @classmethod
    async def from_model(cls, model: BaseModel) -> "FullGroupResponse":
        from app.schema.user import UserResponse
        from app.service import userService

        data = model.model_dump()
        users = await userService.find_many(
            conditions={"group.$id": {"$in": [model.id]}},
        )
        for user in users:
            await user.fetch_link("branch")
        users = [UserResponse(**user.model_dump()) for user in users]
        return cls(**data, users=users)
