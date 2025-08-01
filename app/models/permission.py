from typing import List, Optional

from pydantic import Field
from pymongo import IndexModel

from .base import Base


class Permission(Base):
    code: str = Field(..., description="Unique permission code")
    description: Optional[str] = Field(default=None, description="Optional description")

    # Ghi đè __action__ để thêm hành động 'share'
    __action__: List[str] = ["share"]

    class Settings:
        indexes = [IndexModel([("code", 1)], unique=True)]
