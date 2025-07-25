from functools import wraps
from typing import Callable

from fastapi import Request

from app.common.http_exception import HTTP_429_TOO_MANY_REQUESTS
from app.db import LimitManager


def limiter(max_request: int = 5, duration: int = 60):
    """
    Decorator giới hạn số lần gọi một hàm bất kỳ trong khoảng thời gian nhất định.
    Args:
        - max_request (int): Số lượng tối đa cho phép gọi hàm trong khoảng thời gian `duration`. Mặc định là 5.
        - duration (int): Khoảng thời gian (tính bằng giây). Mặc định là 60 giây.
    Note:
        - Hàm được decorator bắt buộc phải nhận tham số `request: Request` (FastAPI).
        - Nếu không có `request`, decorator này sẽ không có tác dụng
    Example:
        ```python
        @limiter(max_request=10, duration=60)
        async def my_endpoint(request: Request):
            ...
        ```
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if request is None:
                raise RuntimeError("This decorator requires the endpoint to receive a FastAPI Request object.")
            key = f"{func.__name__}:{request.state.request_id}"
            if LimitManager.exist(key):
                count_request = int(LimitManager.get(key))
                if count_request + 1 > max_request:
                    message = f"Quá nhiều yêu cầu. Vui lòng thử lại sau {duration} giây."
                    raise HTTP_429_TOO_MANY_REQUESTS(message)
                LimitManager.incr(key)
            else:
                LimitManager.set(key, 1, ex=duration)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
