from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud, models
from app.auth import get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


def _get_owned_expense_or_404(db: Session, expense_id: int, user_id: int) -> models.Expense:
    expense = crud.get_expense(db, expense_id, user_id)
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found.",
        )
    return expense


def _validate_category(db: Session, category_id: int, user_id: int) -> None:
    category = crud.get_category(db, category_id, user_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with id {category_id} does not exist for this user.",
        )


@router.post(
    "/",
    response_model=schemas.ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense (protected)",
)
def create_expense(
    expense_in: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _validate_category(db, expense_in.category_id, current_user.id)
    return crud.create_expense(db, expense_in, current_user.id)


@router.get(
    "/",
    response_model=List[schemas.ExpenseOut],
    summary="List expenses for the logged-in user, with optional filters (protected)",
)
def list_expenses(
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_expenses(db, current_user.id, category_id, start_date, end_date)


@router.get(
    "/summary",
    response_model=schemas.ExpenseSummary,
    summary="Get total spend and per-category breakdown (protected)",
)
def expense_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_summary(db, current_user.id)


@router.get(
    "/{expense_id}",
    response_model=schemas.ExpenseOut,
    summary="Get a single expense by id (protected)",
)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_expense_or_404(db, expense_id, current_user.id)


@router.put(
    "/{expense_id}",
    response_model=schemas.ExpenseOut,
    summary="Update an expense (protected)",
)
def update_expense(
    expense_id: int,
    updates: schemas.ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    expense = _get_owned_expense_or_404(db, expense_id, current_user.id)
    if updates.category_id is not None:
        _validate_category(db, updates.category_id, current_user.id)
    return crud.update_expense(db, expense, updates)


@router.delete(
    "/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an expense (protected)",
)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    expense = _get_owned_expense_or_404(db, expense_id, current_user.id)
    crud.delete_expense(db, expense)
    return None
