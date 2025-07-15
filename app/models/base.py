from datetime import datetime
from typing import Any, List, Optional

from beanie import Document, Insert, PydanticObjectId, Replace, SaveChanges, Update, WriteRules, before_event
from pydantic import Field
from pymongo.client_session import ClientSession


class Base(Document):
    id: Optional[PydanticObjectId] = Field(default=None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Action Permissions
    __action__: List[str] = ["create", "view", "delete", "update"]

    @before_event([Insert, Update, Replace, SaveChanges])
    def set_updated_at(self):
        self.updated_at = datetime.now()

    async def save(
        self,
        session: ClientSession | None = None,
        link_rule: WriteRules = WriteRules.DO_NOTHING,
        ignore_revision: bool = False,
        **kwargs: Any,
    ) -> None:
        self.updated_at = datetime.now()
        return await super().save(session, link_rule, ignore_revision, **kwargs)

    def model_dump(self, *args, **kwargs) -> dict:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(*args, **kwargs)

    @classmethod
    def get_actions(cls) -> List[str]:
        return cls.__action__
