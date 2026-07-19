"""
SQLAlchemy models.

Relationships:
    User (1) --- (many) Category
    User (1) --- (many) Expense
    Category (1) --- (many) Expense

Each user only ever sees their own categories and expenses (enforced in
the CRUD layer / routers, not just at the DB level).
"""
from datetime import datetime, date as date_type

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    categories = relationship(
        "Category", back_populates="owner", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "Expense", back_populates="owner", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", "user_id", name="uq_category_per_user"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="categories")
    expenses = relationship("Expense", back_populates="category")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    date = Column(Date, default=date_type.today, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    owner = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
