from beanie import Link
from pydantic import Field

from app.models.business import Business

from .base import Base


class Branch(Base):
    name: str = Field(..., description="Unique business name")
    address: str = Field(..., description="Business address (street, city, country, postal_code)")
    contact: str = Field(..., description="Contact info (phone, email, website)")
    business: Link[Business]
