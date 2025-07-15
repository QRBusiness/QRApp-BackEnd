from app.models.business import Business, BusinessType
from app.schema.business import BusinessCreate, BusinessTypeCreate, BusinessTypeUpdate, BusinessUpdate
from app.service.base import Service


class BusinessTypeService(Service[BusinessType, BusinessTypeCreate, BusinessTypeUpdate]):
    def __init__(self):
        super().__init__(BusinessType)


class BusinessService(Service[Business, BusinessCreate, BusinessUpdate]):
    def __init__(self):
        super().__init__(Business)


businessTypeService = BusinessTypeService()
businessService = BusinessService()

__all__ = ["businessTypeService", "businessService"]
