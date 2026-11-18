from datetime import date

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator

import main as tracker


app = FastAPI(title="Expense Tracker API")


class MoneyInput(BaseModel):
    amount: str
    category: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        tracker.parse_amount(value)
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        return tracker.validate_category(value)


class ExpenseInput(MoneyInput):
    expense_date: str = ""
    description: str = ""

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                raise ValueError("Expense date must be in YYYY-MM-DD format.") from None
        return value


class BudgetInput(MoneyInput):
    month: str

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        return tracker.validate_month(value)


@app.get("/api/summary")
def get_summary(month: str = Query(...)):
    try:
        return tracker.monthly_summary(month)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/expenses")
def get_expenses(month: str = "", category: str = ""):
    try:
        return tracker.list_expenses(month, category)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/expenses", status_code=201)
def create_expense(expense: ExpenseInput):
    try:
        return tracker.add_expense(expense.amount, expense.category, expense.expense_date, expense.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/expenses/{expense_id}")
def remove_expense(expense_id: int):
    result = tracker.delete_expense(expense_id)
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return result


@app.put("/api/budgets")
def update_budget(budget: BudgetInput):
    try:
        return tracker.set_budget(budget.month, budget.category, budget.amount)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error