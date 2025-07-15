from typing import Optional

from pydantic import BaseModel, Field

from app.schema import BaseResponse


class PaymentCreate(BaseModel):
    accountNo: str = Field(
        ...,
        min_length=6,
        max_length=19,
        description="Số tài khoản ngân hàng",
    )
    accountName: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=50,
        description="Tên tài khoản ngân hàng",
    )
    acqId: int = Field(alias="bin", ge=100000, le=999999, description="Mã định danh ngân hàng")


class PaymentUpdate(BaseModel):
    pass


class PaymentResponse(BaseResponse):
    accountNo: str
    accountName: Optional[str] = None
    acqId: int
