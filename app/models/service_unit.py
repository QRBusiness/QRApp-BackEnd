from typing import Optional

from beanie import Link
from pydantic import Field

from app.models import Area
from app.models.base import Base


class ServiceUnit(Base):
    name: str = Field(...)
    qr_code: Optional[str] = Field(default=None)
    available: bool = Field(default=True)
    area: Link[Area]
