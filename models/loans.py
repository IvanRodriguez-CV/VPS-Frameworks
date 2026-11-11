from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Loan(SQLModel, table=True):
    __tablename__ = "loans"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    copy_id: int = Field(foreign_key="book_copies.id", index=True)
    loan_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    due_date: datetime
    returned_at: datetime | None = Field(default=None)
    status: str = Field(default="active", max_length=20, index=True)
