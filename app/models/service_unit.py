from typing import Optional

from beanie import Link
from pydantic import Field

from app.models import Area, Branch
from app.models.base import Base


class ServiceUnit(Base):
    name: str = Field(...)
    qr_code: Optional[str] = Field(default=None)
    available: bool = Field(default=True)
    area: Link[Area] = Field(...)
    branch: Link[Branch] = Field(...)
