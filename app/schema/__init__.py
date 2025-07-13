from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )
    id: Optional[str] = Field(alias="_id")
    created_at: Optional[datetime] = None 
    updated_at: Optional[datetime] = None

    @field_validator("id", mode="before")
    @classmethod
    def parse_object_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v
