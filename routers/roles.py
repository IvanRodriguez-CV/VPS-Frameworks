from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from config.dependencies import AdminDependency, SessionDependency
from models import Role, User
from schemas import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_or_404(session: SessionDependency, role_id: int) -> Role:
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado.",
        )
    return role


@router.get("/", response_model=list[RoleRead])
def list_roles(
    session: SessionDependency,
    admin: AdminDependency,
) -> list[Role]:
    return list(session.exec(select(Role).order_by(Role.id)).all())


@router.post(
    "/",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    data: RoleCreate,
    session: SessionDependency,
    admin: AdminDependency,
) -> Role:
    if session.exec(select(Role).where(Role.name == data.name)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El rol ya existe.",
        )
    role = Role(name=data.name)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(
    role_id: int,
    data: RoleUpdate,
    session: SessionDependency,
    admin: AdminDependency,
) -> Role:
    role = get_role_or_404(session, role_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes or any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Envía un nombre de rol válido.",
        )
    if "name" in changes:
        existing = session.exec(
            select(Role).where(Role.name == changes["name"])
        ).first()
        if existing and existing.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El rol ya existe.",
            )
    role.sqlmodel_update(changes)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    session: SessionDependency,
    admin: AdminDependency,
) -> None:
    role = get_role_or_404(session, role_id)
    user = session.exec(select(User).where(User.role_id == role_id)).first()
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un rol asignado a usuarios.",
        )
    session.delete(role)
    session.commit()
