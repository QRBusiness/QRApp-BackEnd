import datetime

import jwt
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.core.config import settings


class JWTSecurity:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expires_delta: datetime.timedelta | None = None,
    ):
        self._algorithm = algorithm
        self._expires_delta = expires_delta
        self._secret_key = secret_key

    def encode(self, payload: dict | BaseModel, expires_delta: datetime.timedelta | None = None) -> str:
        if expires_delta is None:
            expires_delta = self._expires_delta
        if isinstance(payload, dict):
            to_encode = payload.copy()
        else:
            to_encode = jsonable_encoder(payload)
        expire = datetime.datetime.now(datetime.timezone.utc) + (
            expires_delta if expires_delta else datetime.timedelta(minutes=15)
        )
        to_encode.update({"exp": expire})
        token = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return token

    def decode(self, token: str):
        return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])


ACCESS_JWT = JWTSecurity(
    secret_key=settings.ACCESS_KEY,
    expires_delta=datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
)
REFRESH_JWT = JWTSecurity(
    secret_key=settings.REFRESH_KEY,
    expires_delta=datetime.timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
)
