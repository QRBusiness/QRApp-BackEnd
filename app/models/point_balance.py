from beanie import Link
from pydantic import Field
from pymongo import IndexModel

from app.models.base import Base
from app.models.business import Business


class PointBalance(Base):
    phone: str = Field(...)
    balance: float = Field(...)
    business: Link[Business] = Field(..., description="Tích điểm ở doanh nghiệp")

    class Settings:
        indexes = [
            IndexModel(
                [
                    ("phone", 1),
                    ("business", 1),
                ],
                unique=True,
            )
        ]
