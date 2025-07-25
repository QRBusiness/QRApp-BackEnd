from typing import List

from beanie import Document, init_beanie
from loguru import logger
from pymongo import AsyncMongoClient
from pymongo.errors import BulkWriteError

from app.core.config import settings
from app.models import (
    Area,
    Branch,
    Business,
    BusinessType,
    Category,
    ExtendOrder,
    Group,
    Order,
    Payment,
    Permission,
    Plan,
    Product,
    Request,
    ServiceUnit,
    SubCategory,
    User,
)
from app.schema.user import Administrator
from app.service import permissionService, userService


class MongoDB:
    def __init__(
        self,
        url: str,
        database: str,
        documents: List[Document],
    ):
        self.client = AsyncMongoClient(url)
        self.database = database
        self.documents = documents

    async def initialize(self):
        await init_beanie(
            database=self.client[self.database],
            document_models=self.documents,
        )
        # Init Permission
        permissions = []
        for document in self.documents:
            for action in document.get_actions():
                code = f"{action.lower()}.{document.__name__.lower()}"
                description = f"{action.upper()} {document.__name__.upper()}"
                if await permissionService.find_one({"code": code}) is None:
                    permissions.append(Permission(code=code, description=description))
        try:
            if permissions:
                await permissionService.insert_many(permissions)
        except BulkWriteError:
            pass
        except Exception as e:
            logger.error(e)
        # Init Admin
        if not await userService.find_one({"username": "admin"}):
            await userService.insert(
                Administrator(
                    username=settings.ADMIN_USERNAME,
                    password=settings.ADMIN_PASSWORD,
                )
            )
        return self


Mongo = MongoDB(
    url=settings.MONGO_URL,
    database=settings.MONGO_DATABASE,
    documents=[
        User,
        Permission,
        Group,
        BusinessType,
        Business,
        Branch,
        Area,
        ServiceUnit,
        Category,
        SubCategory,
        Product,
        Request,
        Order,
        Payment,
        Plan,
        ExtendOrder,
    ],
)
