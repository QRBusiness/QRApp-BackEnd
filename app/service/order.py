from app.models.order import ExtendOrder, Order
from app.schema.order import ExtenOrderCreate, ExtenOrderUpdate, OrderCreate, OrderUpdate
from app.service.base import Service


class ExtendOrderService(Service[ExtendOrder, ExtenOrderCreate, ExtenOrderUpdate]):
    def __init__(self):
        super().__init__(ExtendOrder)


class OrderService(Service[Order, OrderCreate, OrderUpdate]):
    def __init__(self):
        super().__init__(Order)


orderService = OrderService()
extendOrderService = ExtendOrderService()
__all__ = ["orderService", "extendOrderService"]
