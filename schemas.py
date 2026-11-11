from datetime import datetime, timezone

from pydantic import EmailStr, field_validator, model_validator
from sqlmodel import Field, SQLModel


def validate_password_size(password: str | None) -> str | None:
    if password is not None and len(password.encode("utf-8")) > 72:
        raise ValueError("La contraseña no puede superar 72 bytes en UTF-8.")
    return password


class UserRegister(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    nombre: str = Field(min_length=1, max_length=80)
    apellido: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_hash(cls, value: str) -> str:
        validate_password_size(value)
        return value


class UserCreate(UserRegister):
    role_id: int


class UserUpdate(SQLModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    apellido: str | None = Field(default=None, min_length=1, max_length=80)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role_id: int | None = None

    @field_validator("password")
    @classmethod
    def password_fits_hash(cls, value: str | None) -> str | None:
        return validate_password_size(value)


class UserRead(SQLModel):
    id: int
    username: str
    nombre: str
    apellido: str
    email: EmailStr
    role_id: int
    role: str


class UserIdentity(SQLModel):
    id: int
    username: str
    role_id: int
    role: str


class TokenRead(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserIdentity


class RoleCreate(SQLModel):
    name: str = Field(min_length=1, max_length=30)


class RoleUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)


class RoleRead(SQLModel):
    id: int
    name: str


class AuthorCreate(SQLModel):
    name: str = Field(min_length=1, max_length=120)


class AuthorUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)


class AuthorRead(SQLModel):
    id: int
    name: str


class CategoryCreate(SQLModel):
    name: str = Field(min_length=1, max_length=80)


class CategoryUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)


class CategoryRead(SQLModel):
    id: int
    name: str


class BookCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    author_id: int
    category_id: int
    copies_count: int = Field(default=1, ge=1, le=50)


class BookUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    author_id: int | None = None
    category_id: int | None = None


class BookRead(SQLModel):
    id: int
    title: str
    description: str | None
    author_id: int
    category_id: int


class CopyCreate(SQLModel):
    inventory_code: str | None = Field(default=None, min_length=1, max_length=40)


class CopyRead(SQLModel):
    id: int
    inventory_code: str
    book_id: int
    is_available: bool


class LoanCreate(SQLModel):
    copy_id: int
    due_date: datetime

    @model_validator(mode="after")
    def due_date_is_future(self) -> "LoanCreate":
        if self.due_date.tzinfo is None or self.due_date.utcoffset() is None:
            raise ValueError("La fecha de devolución debe incluir zona horaria.")
        if self.due_date.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("La fecha de devolución debe ser futura.")
        return self


class LoanRead(SQLModel):
    id: int
    user_id: int
    copy_id: int
    book_id: int
    loan_date: datetime
    due_date: datetime
    returned_at: datetime | None
    status: str
