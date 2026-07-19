"""
CRUD helpers. Keeping DB queries here (instead of inline in routers)
keeps route handlers thin and makes the query logic independently
testable/reusable.
"""
from typing import Optional, List
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas


# ---------- Users ----------

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, username: str, hashed_password: str) -> models.User:
    user = models.User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Categories ----------

def get_categories(db: Session, user_id: int) -> List[models.Category]:
    return db.query(models.Category).filter(models.Category.user_id == user_id).all()


def get_category(db: Session, category_id: int, user_id: int) -> Optional[models.Category]:
    return (
        db.query(models.Category)
        .filter(models.Category.id == category_id, models.Category.user_id == user_id)
        .first()
    )


def get_category_by_name(db: Session, name: str, user_id: int) -> Optional[models.Category]:
    return (
        db.query(models.Category)
        .filter(models.Category.name == name, models.Category.user_id == user_id)
        .first()
    )


def create_category(db: Session, category: schemas.CategoryCreate, user_id: int) -> models.Category:
    db_category = models.Category(name=category.name, user_id=user_id)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category: models.Category) -> None:
    db.delete(category)
    db.commit()


# ---------- Expenses ----------

def get_expenses(
    db: Session,
    user_id: int,
    category_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[models.Expense]:
    query = db.query(models.Expense).filter(models.Expense.user_id == user_id)
    if category_id is not None:
        query = query.filter(models.Expense.category_id == category_id)
    if start_date is not None:
        query = query.filter(models.Expense.date >= start_date)
    if end_date is not None:
        query = query.filter(models.Expense.date <= end_date)
    return query.order_by(models.Expense.date.desc()).all()


def get_expense(db: Session, expense_id: int, user_id: int) -> Optional[models.Expense]:
    return (
        db.query(models.Expense)
        .filter(models.Expense.id == expense_id, models.Expense.user_id == user_id)
        .first()
    )


def create_expense(db: Session, expense: schemas.ExpenseCreate, user_id: int) -> models.Expense:
    db_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        date=expense.date or date.today(),
        category_id=expense.category_id,
        user_id=user_id,
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def update_expense(db: Session, expense: models.Expense, updates: schemas.ExpenseUpdate) -> models.Expense:
    data = updates.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: models.Expense) -> None:
    db.delete(expense)
    db.commit()


def get_summary(db: Session, user_id: int) -> dict:
    rows = (
        db.query(
            models.Category.name,
            func.coalesce(func.sum(models.Expense.amount), 0.0),
            func.count(models.Expense.id),
        )
        .join(models.Expense, models.Expense.category_id == models.Category.id)
        .filter(models.Category.user_id == user_id)
        .group_by(models.Category.name)
        .all()
    )
    by_category = [{"category": name, "total": total, "count": count} for name, total, count in rows]
    total_spent = sum(item["total"] for item in by_category)
    return {"total_spent": total_spent, "by_category": by_category}
