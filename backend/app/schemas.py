"""
Pydantic schemas — separate "Create" (input) and "Out" (output) models
so we never leak fields like hashed_password back to the client, and so
validation rules are explicit for every request body.
"""
from datetime import date as date_type, datetime
from typing import Optional, List

from pydantic import BaseModel, Field, ConfigDict


# ---------- Auth / User ----------

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Category ----------

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


# ---------- Expense ----------

class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0, description="Must be greater than 0")
    description: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date_type] = None
    category_id: int


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=255)
    date: Optional[date] = None
    category_id: Optional[int] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: float
    description: Optional[str]
    date: date_type
    category: CategoryOut


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class ExpenseSummary(BaseModel):
    total_spent: float
    by_category: List[CategorySummary]
