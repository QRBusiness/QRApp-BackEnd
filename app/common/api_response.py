from typing import Generic, Optional, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, model_validator

from app.common.api_message import KeyResponse
from app.core.config import settings

Object = TypeVar("T")


class GlobalJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        encoded = jsonable_encoder(content)

        if isinstance(encoded, dict) and encoded.get("pagination") is None:
            encoded.pop("pagination")

        return super().render(encoded)


class Pagination(BaseModel):
    current_page: int = 1
    per_page: int = settings.PAGE_SIZE
    total_items: int
    total_pages: Optional[int] = None

    @model_validator(mode="after")
    def compute_total_pages(self) -> "Pagination":
        from math import ceil

        self.total_pages = max(ceil(self.total_items / self.per_page), 1)
        return self


class Response(BaseModel, Generic[Object]):
    model_config = ConfigDict(
        exclude_none=True,
    )
    message: str = KeyResponse.SUCCESS
    data: Optional[Object] = None
    pagination: Optional[Pagination] = None
