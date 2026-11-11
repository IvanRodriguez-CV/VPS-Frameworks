from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from config.dependencies import AdminDependency, CurrentUser, SessionDependency
from lib.pwd import hash_password
from models import Loan, Role, User
from routers.auth import ensure_unique_user, user_response
from schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Usuarios"])


def get_user_or_404(session: SessionDependency, user_id: int) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    return user


@router.get("/", response_model=list[UserRead])
def list_users(
    session: SessionDependency,
    admin: AdminDependency,
) -> list[UserRead]:
    users = session.exec(select(User).order_by(User.id)).all()
    results: list[UserRead] = []
    for user in users:
        role = session.get(Role, user.role_id)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un usuario no tiene un rol válido.",
            )
        results.append(user_response(user, role))
    return results


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    session: SessionDependency,
    admin: AdminDependency,
) -> UserRead:
    ensure_unique_user(session, data.username, str(data.email))
    role = session.get(Role, data.role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado.",
        )
    user = User(
        username=data.username,
        nombre=data.nombre,
        apellido=data.apellido,
        email=str(data.email),
        password_hash=hash_password(data.password),
        role_id=role.id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user_response(user, role)


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> UserRead:
    user = get_user_or_404(session, user_id)
    if user.id != current_user.id:
        role = session.get(Role, current_user.role_id)
        if role is None or role.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para consultar este usuario.",
            )
    user_role = session.get(Role, user.role_id)
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario no tiene un rol válido.",
        )
    return user_response(user, user_role)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserUpdate,
    session: SessionDependency,
    current_user: CurrentUser,
) -> UserRead:
    user = get_user_or_404(session, user_id)
    current_role = session.get(Role, current_user.role_id)
    is_admin = current_role is not None and current_role.name == "admin"
    if user.id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este usuario.",
        )

    changes = data.model_dump(exclude_unset=True)
    if not is_admin and "role_id" in changes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un administrador puede cambiar roles.",
        )
    if any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Los campos enviados no pueden ser nulos.",
        )

    username = changes.get("username", user.username)
    email = str(changes.get("email", user.email))
    ensure_unique_user(session, username, email, excluded_user_id=user.id)
    if "role_id" in changes and session.get(Role, changes["role_id"]) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado.",
        )
    if "password" in changes:
        changes["password_hash"] = hash_password(changes.pop("password"))

    user.sqlmodel_update(changes)
    session.add(user)
    session.commit()
    session.refresh(user)
    user_role = session.get(Role, user.role_id)
    if user_role is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario no tiene un rol válido.",
        )
    return user_response(user, user_role)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    session: SessionDependency,
    admin: AdminDependency,
) -> None:
    user = get_user_or_404(session, user_id)
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes eliminar tu propia cuenta.",
        )
    loan = session.exec(select(Loan).where(Loan.user_id == user_id)).first()
    if loan is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un usuario con historial de préstamos.",
        )
    session.delete(user)
    session.commit()
