from typing import Annotated, Callable

import jwt
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from database import get_session
from models import Role, User
from config.segurity import decode_access_token, oauth2_scheme

SessionDependency = Annotated[Session, Depends(get_session)]
TokenDependency = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(token: TokenDependency, session: SessionDependency) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise credentials_error from None

    user = session.get(User, user_id)
    if user is None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str) -> Callable:
    def role_dependency(
        current_user: CurrentUser,
        session: SessionDependency,
    ) -> User:
        role = session.get(Role, current_user.role_id)
        if role is None or role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para realizar esta operación.",
            )
        return current_user

    return role_dependency


AdminDependency = Annotated[User, Depends(require_roles("admin"))]
CatalogManagerDependency = Annotated[
    User, Depends(require_roles("admin", "librarian"))
]
