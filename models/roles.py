from sqlmodel import Field, SQLModel


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=30, unique=True, index=True)
