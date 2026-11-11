import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import Session, select

from config.segurity import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY_TOKEN
from database import create_db_and_tables, engine
from lib.pwd import hash_password
from models import Role, User
from routers import auth, catalog, loans, roles, users


def seed_initial_data() -> None:
    with Session(engine) as session:
        for role_name in ("admin", "librarian", "user"):
            role = session.exec(
                select(Role).where(Role.name == role_name)
            ).first()
            if role is None:
                session.add(Role(name=role_name))
        session.commit()

        username = os.getenv("INITIAL_ADMIN_USERNAME", "").strip()
        password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
        if bool(username) != bool(password):
            raise RuntimeError(
                "Configura INITIAL_ADMIN_USERNAME e INITIAL_ADMIN_PASSWORD juntos."
            )
        if not username:
            return
        if session.exec(select(User).where(User.username == username)).first():
            return
        admin_role = session.exec(
            select(Role).where(Role.name == "admin")
        ).first()
        if admin_role is None:
            raise RuntimeError("No fue posible crear el rol administrador.")
        admin = User(
            username=username,
            nombre=os.getenv("INITIAL_ADMIN_NOMBRE", "Administrador"),
            apellido=os.getenv("INITIAL_ADMIN_APELLIDO", "Biblioteca"),
            email=os.getenv(
                "INITIAL_ADMIN_EMAIL", "admin@example.com"
            ).strip(),
            password_hash=hash_password(password),
            role_id=admin_role.id,
        )
        session.add(admin)
        session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not SECRET_KEY_TOKEN:
        raise RuntimeError("Configura SECRET_KEY_TOKEN en el archivo .env.")
    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES debe ser mayor que cero.")
    create_db_and_tables()
    seed_initial_data()
    yield


app = FastAPI(
    title="API REST del Sistema Bibliotecario",
    description="Gestión de usuarios, catálogo, ejemplares y préstamos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(catalog.router)
app.include_router(loans.router)


@app.get("/", tags=["Estado"])
def read_root() -> dict[str, str]:
    return {"message": "API REST del Sistema Bibliotecario"}
