import json
import time
import traceback
from datetime import datetime
from typing import Any, Dict

import httpx
import sentry_sdk
from bson import DBRef
from fastapi import Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from minio.error import S3Error
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.api_message import KeyResponse, get_message


class LoggingMiddleware(BaseHTTPMiddleware):
    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract common request information"""
        h = request.headers
        x_forwarded_for = request.headers.get("x-forwarded-for")
        real_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.client.host
        return {
            "request_id": getattr(request.state, "request_id", None),
            "client_ip": real_ip,
            "x_forwarded_for": x_forwarded_for,
            "x_real_ip": h.get("x-real-ip"),
            "forwarded_proto": h.get("x-forwarded-proto"),
            "forwarded_port": h.get("x-forwarded-port"),
            "forwarded_host": h.get("x-forwarded-host"),
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "user_agent": h.get("user-agent"),
            "referer": h.get("referer"),
            "origin": h.get("origin"),
        }

    async def dispatch(self, request: Request, call_next):
        request_time = datetime.now()
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            log_data = {
                "timestamp": request_time.isoformat(),
                **self._get_request_info(request),
                "duration": duration,
                "status_code": response.status_code,
                "error": None,
                "detail": None,
            }
            logger.info(json.dumps(log_data))
            return response
        except Exception as e:
            duration = time.time() - start_time
            status_code = 500
            error = KeyResponse.SERVER_ERROR
            message = get_message(KeyResponse.SERVER_ERROR)
            if isinstance(e, httpx.ConnectTimeout):
                message = "Hệ thống đang bận, vui lòng thử lại sau."
            if isinstance(e, S3Error):
                message = e.message
            elif isinstance(e, ResponseValidationError):
                status_code = 422
                error = KeyResponse.VALIDATION_ERROR
                message = [f"{error['msg']} {error['loc']}" for error in e.errors()]
            elif isinstance(e, ValidationError):
                status_code = 422
                error = KeyResponse.VALIDATION_ERROR
                message = [f"{error['msg']} {error['loc']}" for error in e.errors()]
            elif isinstance(e, DuplicateKeyError):

                def conflict_message(details: dict) -> str:
                    key_value = details.get("keyValue", {})
                    if not key_value:
                        return "Trùng dữ liệu."
                    messages = []
                    for key, value in key_value.items():
                        if isinstance(value, DBRef):
                            continue
                        messages.append(f"Trùng lặp dữ liệu tại '{key}'")
                    if messages:
                        return "; ".join(messages)
                    return "Trùng dữ liệu."

                status_code = 409
                error = KeyResponse.CONFLICT
                message = conflict_message(e.details)
            elif isinstance(e, PyMongoError):
                message = "Không thể xử lý yêu cầu. Vui lòng thử lại sau."
            else:
                sentry_sdk.capture_exception(e)
            log_data = {
                "timestamp": request_time.isoformat(),
                **self._get_request_info(request),
                "duration": duration,
                "status_code": status_code,
                "error": type(e).__name__,
                "detail": traceback.format_exc().split("\n")[-2],
            }
            logger.error(json.dumps(log_data))
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": error,
                    "message": message,
                },
            )
