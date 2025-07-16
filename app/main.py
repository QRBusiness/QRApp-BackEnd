from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api
from app.common.api_message import KeyResponse
from app.common.http_exception import HTTP_ERROR
from app.core.config import settings
from app.core.middleware import LoggingMiddleware, TraceMiddleware
from app.db import Mongo
from app.socket import manager


@asynccontextmanager
async def lifespan(_: FastAPI):
    # on_startup
    await Mongo.initialize()
    yield
    # on_shutdown


sentry_sdk.init(
    dsn="https://133542f745a7150d8828eda864d3c33c@o4509676361023488.ingest.us.sentry.io/4509676365873152",
    send_default_pii=True,
    server_name=settings.APP_NAME,
    release=settings.APP_VERSION,
    attach_stacktrace=True,
    spotlight=True,
)
app = FastAPI(
    title="QRApp Backend",
    description="""
### 🔹 Tính năng

- **Quản lý doanh nghiệp**
  Tạo và quản lý thông tin doanh nghiệp, chi nhánh, khu vực, bàn/phòng (service unit).

- **Quản lý người dùng & phân quyền**
  Đăng ký, đăng nhập, phân quyền theo nhóm (quản lý, nhân viên, kế toán, ...)
  Kiểm soát truy cập theo vai trò, chi nhánh.

- **Quản lý sản phẩm & menu**
  Thêm, sửa, xóa sản phẩm, phân loại, xây dựng menu động cho từng chi nhánh.

- **Đặt món & xử lý đơn hàng**
  Đặt món qua QR code, tạo đơn hàng, cập nhật trạng thái, xử lý thanh toán

- **Yêu cầu phục vụ & tương tác real-time**
  Gửi yêu cầu phục vụ, gọi món, thanh toán, kết nối qua WebSocket

- **Quản lý nhóm quyền**
  Tạo nhóm, gán quyền, kiểm soát truy cập chi tiết tới từng chức năng.

---

### 🔒 Bảo mật

- Xác thực JWT, phân quyền chặt chẽ theo doanh nghiệp, chi nhánh, nhóm và vai trò.
- Quản lý phiên đăng nhập, kiểm soát truy cập API và WebSocket.

---

### 📚 Tài liệu

- Swagger UI: `/docs`
- ReDoc: `/redoc`
""",
    debug=False,
    lifespan=lifespan,
    version=settings.APP_VERSION,
)
# Middleware
app.add_middleware(TraceMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_HOST],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# API Endpoint
app.include_router(api)


# WebSocket
@app.websocket("/ws")
async def websocket(websocket: WebSocket):
    try:
        if await manager.connect(websocket):
            while True:
                await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


# Handle Exception
@app.exception_handler(HTTP_ERROR)
async def exception_handler(_: Request, exc: HTTP_ERROR):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": KeyResponse.VALIDATION_ERROR,
            "error": [f"{error['msg']} {error['loc']}" for error in exc.errors()],
        },
    )
