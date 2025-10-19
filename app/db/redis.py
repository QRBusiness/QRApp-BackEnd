from typing import List

import redis
from app.core.config import settings


class RedisClient:
    def __init__(self, url, prefix: str | None = None, **kwargs):
        self.client = redis.Redis.from_url(url, **kwargs)
        self.prefix = prefix or ""  # nếu không có prefix thì dùng chuỗi rỗng

    def _format_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def set(self, key, value, **kwargs) -> bool:
        key = self._format_key(key)
        return self.client.set(key, value, **kwargs)

    def get(self, key):
        key = self._format_key(key)
        return self.client.get(key)

    def delete(self, key: str | List[str]):
        if isinstance(key, list):
            keys = [self._format_key(k) for k in key]
            return self.client.delete(*keys)
        else:
            return self.client.delete(self._format_key(key))

    def exist(self, key):
        key = self._format_key(key)
        return self.client.exists(key) == 1


class SessionClient(RedisClient):
    def __init__(self, url, **kwargs):
        super().__init__(url, "session:", **kwargs)

    def sign_in(self, user_id, token: str) -> bool:
        return self.set(
            user_id,
            token,
            nx=True,
            ex=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        )

    def sign_out(self, user_id):
        return self.delete(user_id)


class TrackingClient(RedisClient):
    def __init__(self, url, **kwargs):
        super().__init__(url, "request:", **kwargs)

    def incr(self, key):
        key = self._format_key(key)
        return self.client.incr(key)


SessionManager = SessionClient(settings.REDIS_URL, decode_responses=True)

LimitManager = TrackingClient(settings.REDIS_URL, decode_responses=True)
