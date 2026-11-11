from sqlmodel import Field, SQLModel


class Author(SQLModel, table=True):
    __tablename__ = "authors"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=120, index=True)


class Category(SQLModel, table=True):
    __tablename__ = "categories"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=80, unique=True, index=True)


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, index=True)
    description: str | None = Field(default=None, max_length=2000)
    author_id: int = Field(foreign_key="authors.id", index=True)
    category_id: int = Field(foreign_key="categories.id", index=True)


class BookCopy(SQLModel, table=True):
    __tablename__ = "book_copies"

    id: int | None = Field(default=None, primary_key=True)
    inventory_code: str = Field(max_length=40, unique=True, index=True)
    book_id: int = Field(foreign_key="books.id", index=True)
    is_available: bool = Field(default=True)
