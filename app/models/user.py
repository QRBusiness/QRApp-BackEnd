from typing import List, Literal, Optional

import bcrypt
from beanie import Insert, Link, before_event
from pydantic import Field
from pymongo import IndexModel

from app.models.branch import Branch
from app.models.business import Business
from app.models.group import Group
from app.models.permission import Permission

from .base import Base


class User(Base):
    username: str = Field(nullable=False,unique=True)
    password: str = Field(nullable=False)
    name: Optional[str] = Field(default=None,nullable=True)
    phone: Optional[str] = Field(default=None,nullable=True)
    address:Optional[str] = Field(default=None,nullable=True)
    image_url: Optional[str] = Field(default=None)
    role: Literal['Admin','BusinessOwner','Staff'] = Field(default='Staff')
    available: bool = Field(True)
    permissions: List[Link[Permission]] = Field(default_factory=list)
    branch: Optional[Link[Branch]] = Field(default=None)
    group: List[Link[Group]] = Field(default_factory=list)
    business: Optional[Link[Business]] = Field(default=None)

    class Settings:
        indexes = [
            IndexModel([("username", 1)], unique=True),
            IndexModel([("phone", 1)], unique=True)
        ]

    @before_event(Insert)
    def hash_password(self):
        if self.role not in ['Admin','BusinessOwner','Staff']:
            raise Exception("Role")
        if not self.password.startswith("$2b$"):
            self.password = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def verify_password(self,password:str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))