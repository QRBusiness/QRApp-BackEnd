from pydantic import Field
from pymongo import IndexModel

from .base import Base


class Plan(Base):
    name: str = Field(...)
    period: int = Field(...)
    price: float = Field(...)

    class Settings:
        indexes = [IndexModel([("name", 1)], unique=True), IndexModel([("period", 1)], unique=True)]
