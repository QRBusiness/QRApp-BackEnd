from typing import List, Literal, Optional

import bcrypt
from beanie import Insert, Link, before_event
from pydantic import Field
from pymongo import IndexModel
from typing_extensions import Self

from app.common.http_exception import HTTP_400_BAD_REQUEST
from app.models.branch import Branch
from app.models.business import Business
from app.models.group import Group
from app.models.permission import Permission

from .base import Base


class User(Base):
    username: str = Field(nullable=False, unique=True)
    password: str = Field(nullable=False)
    name: Optional[str] = Field(default=None, nullable=True)
    phone: Optional[str] = Field(default=None, nullable=True)
    email: Optional[str] = Field(default=None, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    email_verified: bool = Field(default=False)
    address: Optional[str] = Field(default=None, nullable=True)
    image_url: Optional[str] = Field(default=None)
    role: Literal["Admin", "BusinessOwner", "Staff"] = Field(default="Staff")
    available: bool = Field(True)
    permissions: List[Link[Permission]] = Field(default_factory=list)
    branch: Optional[Link[Branch]] = Field(default=None)
    group: List[Link[Group]] = Field(default_factory=list)
    business: Optional[Link[Business]] = Field(default=None)

    class Settings:
        indexes = [
            IndexModel([("username", 1)], unique=True),
        ]

    @before_event(Insert)
    def hash_password(self):
        # Validation Data
        import re

        EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        PHONE_REGEX = re.compile(r"^(0[3|5|7|8|9])[0-9]{8}$")
        PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,32}$")
        if self.email and not EMAIL_REGEX.fullmatch(self.email):
            raise HTTP_400_BAD_REQUEST("Email không hợp lệ")
        # Validate phone
        if self.phone and not PHONE_REGEX.fullmatch(self.phone):
            raise HTTP_400_BAD_REQUEST("Số điện thoại không hợp lệ")
        # Validate password
        if not PASSWORD_REGEX.fullmatch(self.password):
            raise HTTP_400_BAD_REQUEST("Mật khẩu dài từ 6-32 kí tự (Gồm chữ hoa, thường, số)")
        if not self.password.startswith("$2b$"):
            self.password = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def change_password(self, new_password: str) -> Self:
        if not new_password.startswith("$2b$"):
            self.password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        return self

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))
