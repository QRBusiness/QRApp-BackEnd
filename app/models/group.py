from typing import List, Optional

from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models.business import Business
from app.models.permission import Permission

from .base import Base


class Group(Base):
    name: str
    description: Optional[str] = Field(default=None, description="Optional description")
    business: Optional[Link[Business]] = Field(default=None)
    permissions: List[Link[Permission]] = Field(
        default_factory=list,
    )

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("name", 1),
                    ("business", 1),
                ],
                unique=True,
            )
        ]
