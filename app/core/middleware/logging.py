import json
import time
from typing import Any, Dict

import httpx
from fastapi import Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.api_message import KeyResponse, get_message


class LoggingMiddleware(BaseHTTPMiddleware):
    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract common request information"""
        return {
            "request_id": request.state.request_id,
            "host": request.client.host,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "method": request.method,
            "path": request.url.path,
        }

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            log_data = {
                **self._get_request_info(request),
                "duration": duration,
                "status_code": response.status_code,
                "error": None,
            }
            logger.info(json.dumps(log_data))
            return response
        except Exception as e:
            duration = time.time() - start_time
            status_code = 500
            error = KeyResponse.SERVER_ERROR
            message = get_message(KeyResponse.SERVER_ERROR)
            if isinstance(e,httpx.ConnectTimeout):
                message = "Hệ thống đang bận, vui lòng thử lại sau."
            if isinstance(e,PyMongoError):
                message = "Không thể xử lý yêu cầu. Vui lòng thử lại sau."
            if isinstance(e, ResponseValidationError):
                status_code = 422
                error = KeyResponse.VALIDATION_ERROR
                message = [f"{error['msg']} {error['loc']}" for error in e.errors()]
            if isinstance(e, ValidationError):
                status_code = 422
                error = KeyResponse.VALIDATION_ERROR
                message = [f"{error['msg']} {error['loc']}" for error in e.errors()]
            if isinstance(e, DuplicateKeyError):
                status_code = 409
                error = KeyResponse.CONFLICT
                message = e.details["errmsg"]
            log_data = {
                **self._get_request_info(request),
                "duration": duration,
                "status_code": status_code,
                "error": type(e).__name__,
            }
            logger.error(json.dumps(log_data))
            return JSONResponse(
                status_code=status_code, content={"error": error, "message": message}
            )
