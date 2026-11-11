from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from config.dependencies import CurrentUser, SessionDependency
from config.segurity import create_access_token
from lib.pwd import hash_password, verify_password
from models import Role, User
from schemas import TokenRead, UserIdentity, UserRead, UserRegister

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def user_response(user: User, role: Role) -> UserRead:
    return UserRead(
        id=user.id,
        username=user.username,
        nombre=user.nombre,
        apellido=user.apellido,
        email=user.email,
        role_id=user.role_id,
        role=role.name,
    )


def ensure_unique_user(
    session: Session,
    username: str,
    email: str,
    excluded_user_id: int | None = None,
) -> None:
    existing_username = session.exec(
        select(User).where(User.username == username)
    ).first()
    existing_email = session.exec(select(User).where(User.email == email)).first()
    if (existing_username and existing_username.id != excluded_user_id) or (
        existing_email and existing_email.id != excluded_user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario o correo ya está registrado.",
        )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(data: UserRegister, session: SessionDependency) -> UserRead:
    ensure_unique_user(session, data.username, str(data.email))
    role = session.exec(select(Role).where(Role.name == "user")).first()
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Los roles iniciales no están disponibles.",
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


@router.post("/login", response_model=TokenRead)
def login(
    session: SessionDependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> TokenRead:
    user = session.exec(
        select(User).where(User.username == form_data.username)
    ).first()
    if user is None or not verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role = session.get(Role, user.role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        {"sub": str(user.id), "username": user.username, "role": role.name}
    )
    return TokenRead(
        access_token=token,
        user=UserIdentity(
            id=user.id,
            username=user.username,
            role_id=user.role_id,
            role=role.name,
        ),
    )


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: CurrentUser,
    session: SessionDependency,
) -> UserRead:
    role = session.get(Role, current_user.role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_response(current_user, role)
