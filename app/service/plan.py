from app.models.plan import Plan
from app.schema.plan import PlanCreate, PlanUpdate
from app.service.base import Service


class PlanService(Service[Plan, PlanCreate, PlanUpdate]):
    def __init__(self):
        super().__init__(Plan)

    async def insert(self, data):
        data = data.model_dump()
        data["price"] = data.get("period") * 25000
        return await super().insert(data)


planService = PlanService()

__all__ = ["planService"]
