from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from config.dependencies import CurrentUser, SessionDependency
from models import BookCopy, Loan, Role, User
from schemas import LoanCreate, LoanRead

router = APIRouter(prefix="/loans", tags=["Préstamos"])


def loan_response(session: SessionDependency, loan: Loan) -> LoanRead:
    copy = session.get(BookCopy, loan.copy_id)
    if copy is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El préstamo tiene un ejemplar inválido.",
        )
    return LoanRead(
        id=loan.id,
        user_id=loan.user_id,
        copy_id=loan.copy_id,
        book_id=copy.book_id,
        loan_date=loan.loan_date,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
        status=loan.status,
    )


def can_manage_all_loans(session: SessionDependency, user: User) -> bool:
    role = session.get(Role, user.role_id)
    return role is not None and role.name in {"admin", "librarian"}


def check_loan_access(
    session: SessionDependency,
    loan: Loan,
    user: User,
) -> None:
    if loan.user_id != user.id and not can_manage_all_loans(session, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar este préstamo.",
        )


@router.post(
    "/",
    response_model=LoanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_loan(
    data: LoanCreate,
    session: SessionDependency,
    current_user: CurrentUser,
) -> LoanRead:
    copy = session.get(BookCopy, data.copy_id)
    if copy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ejemplar no encontrado.",
        )
    if not copy.is_available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ejemplar no está disponible.",
        )

    loan = Loan(
        user_id=current_user.id,
        copy_id=copy.id,
        due_date=data.due_date,
        status="active",
    )
    copy.is_available = False
    session.add(loan)
    session.add(copy)
    session.commit()
    session.refresh(loan)
    return loan_response(session, loan)


@router.get("/", response_model=list[LoanRead])
def list_loans(
    session: SessionDependency,
    current_user: CurrentUser,
) -> list[LoanRead]:
    query = select(Loan).order_by(Loan.loan_date.desc())
    if not can_manage_all_loans(session, current_user):
        query = query.where(Loan.user_id == current_user.id)
    loans = session.exec(query).all()
    return [loan_response(session, loan) for loan in loans]


@router.get("/{loan_id}", response_model=LoanRead)
def read_loan(
    loan_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> LoanRead:
    loan = session.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado.",
        )
    check_loan_access(session, loan, current_user)
    return loan_response(session, loan)


@router.post("/{loan_id}/return", response_model=LoanRead)
def return_loan(
    loan_id: int,
    session: SessionDependency,
    current_user: CurrentUser,
) -> LoanRead:
    loan = session.get(Loan, loan_id)
    if loan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado.",
        )
    check_loan_access(session, loan, current_user)
    if loan.status != "active":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El préstamo ya fue devuelto.",
        )
    copy = session.get(BookCopy, loan.copy_id)
    if copy is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El préstamo tiene un ejemplar inválido.",
        )
    loan.status = "returned"
    loan.returned_at = datetime.now(timezone.utc)
    copy.is_available = True
    session.add(loan)
    session.add(copy)
    session.commit()
    session.refresh(loan)
    return loan_response(session, loan)
