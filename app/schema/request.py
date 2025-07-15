from typing import List, Optional

from beanie import Link, PydanticObjectId
from pydantic import BaseModel, Field

from app.models.request import RequestStatus, RequestType
from app.models.user import User
from app.schema import BaseResponse
from app.schema.area import AreaResponse
from app.schema.service_unit import ServiceUnitResponse


class RequestCreate(BaseModel):
    type: RequestType = Field(..., description="Loại yêu cầu")
    reason: Optional[str] = Field(default=None, description="Lý do yêu cầu")
    service_unit: Optional[PydanticObjectId] = None
    guest_name: Optional[str] = Field(default=None)
    area: Optional[PydanticObjectId] = None
    data: List = []


class RequestUpdate(BaseModel):
    status: Optional[RequestStatus] = RequestStatus.COMPLETED
    staff: Optional[Link[User]] = None


class MinimumResquestResponse(BaseResponse):
    type: RequestType
    reason: Optional[str] = None
    status: RequestStatus
    guest_name: Optional[str] = None


class ResquestResponse(BaseResponse):
    type: RequestType
    reason: Optional[str] = None
    status: RequestStatus
    guest_name: Optional[str] = None
    area: AreaResponse
    service_unit: ServiceUnitResponse
    data: List = []
