from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(e)
            return JSONResponse(
                status_code=500,
                content = {
                    "error":e.__class__.__name__,
                    "message": str(e),
                }
            )