from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True, index=True)
    nombre: str = Field(max_length=80)
    apellido: str = Field(max_length=80)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role_id: int = Field(foreign_key="roles.id", index=True)
