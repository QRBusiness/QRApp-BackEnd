from typing import Optional

from pydantic import BaseModel, Field

from app.schema import BaseResponse


class PlanCreate(BaseModel):
    name: str = Field(..., description="Tên gói")
    period: int = Field(..., description="Thời hạn")


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    period: Optional[int] = None
    price: Optional[float] = None


class PlanResponse(BaseResponse):
    name: str = Field(...)
    period: int = Field(...)
    price: float = Field(...)
    qr_code: Optional[str] = Field(default=None)
