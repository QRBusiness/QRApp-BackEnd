from typing import List

from beanie import Document, init_beanie
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import BulkWriteError

from app.core.config import settings
from app.models import (Area, Branch, Business, BusinessType, Category, Group,
                        Order, Permission, Product, Request, ServiceUnit,
                        SubCategory, User)
from app.schema.user import Administrator
from app.service import permissionService, userService


class MongoDB:
    def __init__(
        self,
        url: str,
        database: str,
        documents: List[Document],
    ):
        self.client = AsyncIOMotorClient(
            url,
        )
        self.database = AsyncIOMotorDatabase(
            client=self.client,
            name=database,
        )
        self.documents = documents

    async def initialize(self):
        await init_beanie(
            database=self.database,
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
                    name="Administrator",
                    phone="Administrator",
                    address="Administrator",
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
    ],
)
