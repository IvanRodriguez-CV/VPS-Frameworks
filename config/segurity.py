import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SECRET_KEY_TOKEN = os.getenv("SECRET_KEY_TOKEN", "")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict[str, Any]) -> str:
    if not SECRET_KEY_TOKEN:
        raise RuntimeError("Configura SECRET_KEY_TOKEN en el archivo .env.")
    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser mayor que cero.")
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, SECRET_KEY_TOKEN, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, SECRET_KEY_TOKEN, algorithms=[ALGORITHM])
