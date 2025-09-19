from app.models.point_balance import PointBalance
from app.schema.point_balance import PointBalanceCreate, PointBalanceUpdate
from app.service.base import Service


class PointService(Service[PointBalance, PointBalanceCreate, PointBalanceUpdate]):
    def __init__(self):
        super().__init__(PointBalance)


pointService = PointService()

__all__ = ["pointService"]
