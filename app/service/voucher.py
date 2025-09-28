from app.models.voucher import Voucher
from app.schema.voucher import VoucherCreate, VoucherUpdate
from app.service.base import Service


class VoucherService(Service[Voucher, VoucherCreate, VoucherUpdate]):
    def __init__(self):
        super().__init__(Voucher)


voucherService = VoucherService()

__all__ = ["voucherService"]
