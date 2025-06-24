from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel

from app.schema import BaseResponse
from app.schema.area import AreaResponse


class ServiceUnitCreate(BaseModel):
    name: str
    qr_code: Optional[str] = None
    area: PydanticObjectId

class ServiceUnitUpdate(BaseModel):
    name: Optional[str] = None
    qr_code: Optional[str] = None

class ServiceUnitResponse(BaseResponse):
    name: str
    qr_code: Optional[str] = None
    area: AreaResponse

