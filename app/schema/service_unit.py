from typing import Optional
from urllib.parse import urlparse, urlunparse

from beanie import PydanticObjectId
from pydantic import BaseModel, field_serializer

from app.core.config import settings
from app.schema import BaseResponse
from app.schema.area import AreaResponse


class ServiceUnitCreate(BaseModel):
    name: str
    area: PydanticObjectId


class ServiceUnitUpdate(BaseModel):
    name: Optional[str] = None


class ServiceUnitResponse(BaseResponse):
    name: str
    qr_code: Optional[str] = None
    area: Optional[AreaResponse] = None

    @field_serializer("img_url")
    def serialize_qr_code(self, value: Optional[str]) -> Optional[str]:
        if value is not None:
            parsed = urlparse(value)
            if parsed.netloc == settings.MINIO_ENDPOINT:
                base = urlparse(settings.BASE_URL)
                new_url = parsed._replace(netloc=base.netloc, scheme=base.scheme)
                return urlunparse(new_url)
        return value
