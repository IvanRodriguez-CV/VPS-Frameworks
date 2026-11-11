from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from config.dependencies import (
    CatalogManagerDependency,
    CurrentUser,
    SessionDependency,
)
from models import Author, Book, BookCopy, Category, Loan
from schemas import (
    AuthorCreate,
    AuthorRead,
    AuthorUpdate,
    BookCreate,
    BookRead,
    BookUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CopyCreate,
    CopyRead,
)

router = APIRouter(tags=["Catálogo"])


def get_author_or_404(session: SessionDependency, author_id: int) -> Author:
    author = session.get(Author, author_id)
    if author is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado.",
        )
    return author


def get_category_or_404(session: SessionDependency, category_id: int) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada.",
        )
    return category


def get_book_or_404(session: SessionDependency, book_id: int) -> Book:
    book = session.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado.",
        )
    return book


@router.get("/authors/", response_model=list[AuthorRead])
def list_authors(
    session: SessionDependency,
    current_user: CurrentUser,
) -> list[Author]:
    return list(session.exec(select(Author).order_by(Author.name)).all())


@router.post(
    "/authors/",
    response_model=AuthorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_author(
    data: AuthorCreate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Author:
    author = Author(name=data.name.strip())
    if not author.name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El nombre del autor no puede estar vacío.",
        )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@router.get("/authors/{author_id}", response_model=AuthorRead)
def read_author(
    author_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> Author:
    return get_author_or_404(session, author_id)


@router.patch("/authors/{author_id}", response_model=AuthorRead)
def update_author(
    author_id: int,
    data: AuthorUpdate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Author:
    author = get_author_or_404(session, author_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes or any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Envía un nombre de autor válido.",
        )
    author.name = changes["name"].strip()
    if not author.name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El nombre del autor no puede estar vacío.",
        )
    session.add(author)
    session.commit()
    session.refresh(author)
    return author


@router.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(
    author_id: int,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> None:
    author = get_author_or_404(session, author_id)
    book = session.exec(select(Book).where(Book.author_id == author_id)).first()
    if book is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un autor asociado a libros.",
        )
    session.delete(author)
    session.commit()


@router.get("/categories/", response_model=list[CategoryRead])
def list_categories(
    session: SessionDependency,
    current_user: CurrentUser,
) -> list[Category]:
    return list(session.exec(select(Category).order_by(Category.name)).all())


@router.post(
    "/categories/",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    data: CategoryCreate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Category:
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El nombre de la categoría no puede estar vacío.",
        )
    if session.exec(select(Category).where(Category.name == name)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La categoría ya existe.",
        )
    category = Category(name=name)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.get("/categories/{category_id}", response_model=CategoryRead)
def read_category(
    category_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> Category:
    return get_category_or_404(session, category_id)


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Category:
    category = get_category_or_404(session, category_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes or any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Envía un nombre de categoría válido.",
        )
    name = changes["name"].strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El nombre de la categoría no puede estar vacío.",
        )
    duplicate = session.exec(select(Category).where(Category.name == name)).first()
    if duplicate is not None and duplicate.id != category_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La categoría ya existe.",
        )
    category.name = name
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> None:
    category = get_category_or_404(session, category_id)
    book = session.exec(
        select(Book).where(Book.category_id == category_id)
    ).first()
    if book is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una categoría asociada a libros.",
        )
    session.delete(category)
    session.commit()


@router.get("/books/", response_model=list[BookRead])
def list_books(
    session: SessionDependency,
    current_user: CurrentUser,
) -> list[Book]:
    return list(session.exec(select(Book).order_by(Book.title)).all())


@router.post(
    "/books/",
    response_model=BookRead,
    status_code=status.HTTP_201_CREATED,
)
def create_book(
    data: BookCreate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Book:
    get_author_or_404(session, data.author_id)
    get_category_or_404(session, data.category_id)
    book = Book(
        title=data.title.strip(),
        description=data.description,
        author_id=data.author_id,
        category_id=data.category_id,
    )
    if not book.title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El título del libro no puede estar vacío.",
        )
    session.add(book)
    session.flush()
    for _ in range(data.copies_count):
        session.add(
            BookCopy(
                inventory_code=f"INV-{uuid4().hex[:12].upper()}",
                book_id=book.id,
            )
        )
    session.commit()
    session.refresh(book)
    return book


@router.get("/books/{book_id}", response_model=BookRead)
def read_book(
    book_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> Book:
    return get_book_or_404(session, book_id)


@router.patch("/books/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    data: BookUpdate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> Book:
    book = get_book_or_404(session, book_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes or any(
        key != "description" and value is None for key, value in changes.items()
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Envía al menos un campo válido del libro.",
        )
    if "title" in changes:
        changes["title"] = changes["title"].strip()
        if not changes["title"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="El título del libro no puede estar vacío.",
            )
    if "author_id" in changes:
        get_author_or_404(session, changes["author_id"])
    if "category_id" in changes:
        get_category_or_404(session, changes["category_id"])
    book.sqlmodel_update(changes)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> None:
    book = get_book_or_404(session, book_id)
    copy = session.exec(select(BookCopy).where(BookCopy.book_id == book_id)).first()
    if copy is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Elimina los ejemplares antes de eliminar el libro.",
        )
    session.delete(book)
    session.commit()


@router.get("/books/{book_id}/copies", response_model=list[CopyRead])
def list_book_copies(
    book_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> list[BookCopy]:
    get_book_or_404(session, book_id)
    return list(
        session.exec(
            select(BookCopy)
            .where(BookCopy.book_id == book_id)
            .order_by(BookCopy.id)
        ).all()
    )


@router.post(
    "/books/{book_id}/copies",
    response_model=CopyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_book_copy(
    book_id: int,
    data: CopyCreate,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> BookCopy:
    get_book_or_404(session, book_id)
    inventory_code = data.inventory_code or f"INV-{uuid4().hex[:12].upper()}"
    if session.exec(
        select(BookCopy).where(BookCopy.inventory_code == inventory_code)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El código de inventario ya existe.",
        )
    copy = BookCopy(inventory_code=inventory_code, book_id=book_id)
    session.add(copy)
    session.commit()
    session.refresh(copy)
    return copy


@router.delete("/copies/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_copy(
    copy_id: int,
    session: SessionDependency,
    manager: CatalogManagerDependency,
) -> None:
    copy = session.get(BookCopy, copy_id)
    if copy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejemplar no encontrado.",
        )
    loan = session.exec(select(Loan).where(Loan.copy_id == copy_id)).first()
    if loan is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un ejemplar con historial de préstamos.",
        )
    session.delete(copy)
    session.commit()
