from typing import Optional

from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models import Area, Branch, Business
from app.models.base import Base


class ServiceUnit(Base):
    name: str = Field(...)
    qr_code: Optional[str] = Field(default=None)
    available: bool = Field(default=True)
    area: Link[Area] = Field(...)
    branch: Link[Branch] = Field(...)
    business: Link[Business] = Field(...)

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("name", 1),
                    ("area", 1),
                    ("branch", 1),
                    ("business", 1),
                ],
                unique=True,
            )
        ]
