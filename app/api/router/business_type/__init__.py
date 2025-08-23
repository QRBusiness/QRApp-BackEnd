import io
from typing import List

import pandas as pd
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.dependency import login_required, permission_required, role_required
from app.common.api_response import Pagination, Response
from app.common.http_exception import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from app.core.config import settings
from app.schema.business import BusinessTypeCreate, BusinessTypeResponse, BusinessTypeUpdate
from app.schema.product import Menu
from app.service import businessService, businessTypeService

apiRouter = APIRouter(
    tags=["Business Type"],
    prefix="/business-type",
    dependencies=[
        Depends(login_required),
        Depends(role_required(role=["Admin"])),
    ],
)


@apiRouter.get(
    path="",
    name="Xem danh sách loại doanh nghiệp",
    response_model=Response[List[BusinessTypeResponse]],
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.businesstype"],
            ),
        ),
    ],
)
async def get_business_type(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=settings.PAGE_SIZE, ge=1, le=50),
):
    data = await businessTypeService.find_many(
        conditions={},
        skip=(page - 1) * limit,
        limit=limit,
    )
    return Response(
        data=data,
        pagination=Pagination(
            current_page=page,
            per_page=limit,
            total_items=await businessTypeService.count(
                {},
            ),
        ),
    )


@apiRouter.get(
    path="/{id}",
    name="Xem loại doanh nghiệp",
    response_model=Response[BusinessTypeResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=["view.businesstype"],
            ),
        ),
    ],
)
async def get_business_type_by_id(id: PydanticObjectId):
    data = await businessTypeService.find(id)
    if data is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    return Response(data=data)


@apiRouter.post(
    path="",
    name="Tạo loại doanh nghiệp",
    response_model=Response[BusinessTypeResponse],
    dependencies=[Depends(permission_required(permissions=["create.businesstype"]))],
)
async def post_business_type(data: BusinessTypeCreate | List[BusinessTypeCreate]):
    import re

    if await businessTypeService.find_one({"name": re.compile(f"^{re.escape(data.name)}$", re.IGNORECASE)}):
        raise HTTP_409_CONFLICT(f"{data.name} đã tồn tại")
    data = await businessTypeService.insert(data)
    return Response(data=data)


@apiRouter.post(
    path="/menu/{id}",
    name="Menu Mặc Định",
    response_model=Response[bool],
    dependencies=[
        Depends(
            permission_required(
                permissions=[
                    "update.businesstype",
                ],
            ),
        ),
    ],
)
async def upload_default_menu(
    id: PydanticObjectId,
    menu: UploadFile = File(description="Menu"),
):
    def parse_price_list(price_str):
        if pd.isna(price_str):
            return []
        result = []
        for item in price_str.split(","):
            if ":" in item:
                t, p = item.split(":")
                result.append({"type": t.strip(), "price": int(p)})
        return result

    # -- #
    if await businessTypeService.find(id) is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    menu = await menu.read()
    menu: pd.DataFrame = pd.read_excel(io.BytesIO(menu))
    menu = menu[1:]
    #
    menu_json = {"categories": []}
    for cat, cat_df in menu.groupby("Category"):
        cat_dict = {"name": cat, "description": "", "subcategories": []}
        for sub, sub_df in cat_df.groupby("Subcategory"):
            sub_dict = {"name": sub, "description": "", "products": []}
            for _, row in sub_df.iterrows():
                product = {
                    "name": row["Product"],
                    "description": row["Description"],
                    "variants": parse_price_list(row["Size_Price"]),
                    "options": parse_price_list(row["Options_Price"]),
                    "img_url": row["Image"] if pd.notna(row["Image"]) else None,
                }
                sub_dict["products"].append(product)
            cat_dict["subcategories"].append(sub_dict)
        menu_json["categories"].append(cat_dict)
    # ---- Parse Excel to Json
    menu: Menu = Menu.model_validate(menu_json)
    await businessTypeService.update(id=id, data={"menu": menu})
    return Response(data=True)


@apiRouter.put(
    path="/{id}",
    name="Sửa loại Doanh Nghiệp",
    response_model=Response[BusinessTypeResponse],
    dependencies=[
        Depends(
            permission_required(
                permissions=[
                    "update.businesstype",
                ],
            ),
        ),
    ],
)
async def update_business_type(id: PydanticObjectId, data: BusinessTypeUpdate):
    if await businessTypeService.find(id) is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if data.name:
        if b_type := await businessTypeService.find_one(
            {
                "name": {
                    "$regex": f"^{data.name}$",
                    "$options": "i",
                },
            },
        ):
            if b_type.id != id:
                raise HTTP_409_CONFLICT(f"Loại hình {data.name} đã tồn tại")
    data = await businessTypeService.update(
        id=id,
        data=data.model_dump(exclude_none=True),
    )
    return Response(data=data)


@apiRouter.delete(
    path="/{id}",
    name="Xóa loại Doanh Nghiệp",
    deprecated=True,
    dependencies=[
        Depends(
            permission_required(
                permissions=["delete.businesstype"],
            ),
        ),
    ],
    response_model=Response[str],
)
async def delete_business_type(id: PydanticObjectId):
    b_type = await businessTypeService.find(id)
    if b_type is None:
        raise HTTP_404_NOT_FOUND("Không tìm thấy")
    if await businessService.find_one({"business_type.$id": b_type.id}):
        raise HTTP_400_BAD_REQUEST("Loại doanh nghiệp đang được sử dụng.")
    if not await businessTypeService.delete(id):
        return Response(data="Xóa thất bại")
    return Response(data="Xóa thành công")
