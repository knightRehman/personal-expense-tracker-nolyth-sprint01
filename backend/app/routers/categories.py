from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, crud, models
from app.auth import get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=schemas.CategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense category (protected)",
)
def create_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    existing = crud.get_category_by_name(db, category_in.name, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category_in.name}' already exists.",
        )
    return crud.create_category(db, category_in, current_user.id)


@router.get(
    "/",
    response_model=List[schemas.CategoryOut],
    summary="List all categories for the logged-in user (protected)",
)
def list_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return crud.get_categories(db, current_user.id)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category (protected)",
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    category = crud.get_category(db, category_id, current_user.id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found.",
        )
    if category.expenses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a category that still has expenses linked to it.",
        )
    crud.delete_category(db, category)
    return None
