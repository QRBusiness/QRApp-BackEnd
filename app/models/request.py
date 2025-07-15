from enum import Enum
from typing import List, Optional

from beanie import Link, PydanticObjectId, Save, after_event
from pydantic import Field

from app.models.base import Base


class RequestType(str, Enum):
    ORDER = "Order"  # Dat mon
    REQUEST = "Request"  # CALL STAFF
    PAYMENT = "Payment"  # Thanh toan
    EXTEND = "Extend"  # Gia han


class RequestStatus(str, Enum):
    CANCELLED = "Cancelled"
    WAITING = "Waiting"
    COMPLETED = "Completed"

    def next(self):
        flow = {
            RequestStatus.WAITING: RequestStatus.COMPLETED,
        }
        return flow.get(self, None)

    def cancel(self) -> "RequestStatus":
        """Chuyển trạng thái sang 'Cancelled'."""
        return RequestStatus.CANCELLED


class Request(Base):
    type: RequestType = Field(..., description="Loại yêu cầu (Order / Checkout)")
    reason: Optional[str] = Field(default=None, description="Lý do yêu cầu")
    guest_name: Optional[str] = Field(default=None, description="Tên khách hàng")
    status: RequestStatus = Field(default=RequestStatus.WAITING, description="Trạng thái xử lý")
    staff: Optional["Link[User]"] = Field(default=None, description="Nhân viên xử lý")  # type: ignore  # noqa: F821
    data: Optional[List] = Field(default_factory=list)
    # ---- #
    service_unit: Optional["Link[ServiceUnit]"] = Field(default=None, description="Yêu cầu cho dịch vụ")  # type: ignore  # noqa: F821
    area: Optional["Link[Area]"] = Field(default=None, description="Yêu cầu cho khu vực")  # type: ignore  # noqa: F821
    branch: Optional["Link[Branch]"] = Field(default=None, description="Yêu cầu cho chinh nhánh")  # type: ignore  # noqa: F821
    business: Optional["Link[Business]"] = Field(default=None, description="Yêu cầu cho doanh nghiệp")  # type: ignore  # noqa: F821
    # Ghi đè __action__ để thêm hành động 'share'
    __action__: List[str] = ["view", "receive", "delete", "update"]

    @after_event([Save])
    async def create_order_if_complete(self):
        if self.status == RequestStatus.COMPLETED:
            if self.type == RequestType.ORDER:
                from app.schema.order import OrderCreate
                from app.service import orderService, productService

                # Tạo order ở đây
                product_ids = [PydanticObjectId(product.get("_id")) for product in self.data]
                products = await productService.find_many(conditions={"_id": {"$in": product_ids}})
                product_map = {str(product.id): product for product in products}
                amount = 0
                for product in self.data:
                    db_product = product_map.get(product.get("_id"))
                    variant_price = next(
                        (v.price for v in db_product.variants if v.type == product.get("variant")),
                        0,
                    )
                    option_price_map = {opt.type: opt.price for opt in db_product.options}
                    product_options = product.get("options", [])
                    option_price = sum(option_price_map.get(opt, 0) for opt in product_options)
                    amount = amount + (variant_price + option_price) * product.get("quantity", 1)
                for p in self.data:
                    p["product"] = product_map.get(p.get("_id")).to_ref()
                    del p["_id"]
                await orderService.insert(
                    OrderCreate(
                        items=self.data,
                        amount=amount,
                        business=self.business.to_ref(),
                        branch=self.branch.to_ref(),
                        area=self.area.to_ref(),
                        service_unit=self.service_unit.to_ref(),
                        staff=self.staff.to_ref(),
                        request=self.to_ref(),
                    )
                )
            if self.type == RequestType.EXTEND:
                await orderService.insert(
                    OrderCreate(
                        items=self.data,
                        amount=amount,
                        business=self.business.to_ref(),
                        branch=self.branch.to_ref(),
                        area=self.area.to_ref(),
                        service_unit=self.service_unit.to_ref(),
                        staff=self.staff.to_ref(),
                        request=self.to_ref(),
                    )
                )
