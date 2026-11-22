from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator

from tracker.core import tracker


app = FastAPI(title="Expense Tracker API")


class MoneyInput(BaseModel):
    """Shared amount and category fields for expenses and budgets."""

    amount: str
    category: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        """Require a positive decimal amount with at most two decimal places."""
        tracker.parse_amount(value)
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        """Reject empty categories and normalize their spelling."""
        return tracker.validate_category(value)


class ExpenseInput(MoneyInput):
    """Expense details; an omitted date defaults to today in the tracker."""

    expense_date: str = ""
    description: str = ""

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        """Accept an empty date or a valid date in YYYY-MM-DD format."""
        if value:
            return tracker.validate_expense_date(value)
        return value


class BudgetInput(MoneyInput):
    """A category budget for a month in YYYY-MM format."""

    month: str

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        """Validate the budget's month."""
        return tracker.validate_month(value)


class ExpenseUpdateInput(MoneyInput):
    """Complete replacement fields for an existing expense."""

    expense_date: str
    description: str = ""

    @field_validator("expense_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        return tracker.validate_expense_date(value)


@app.get("/api/summary")
def get_summary(month: str = Query(...)):
    """Return spending and category budget progress for the requested month."""
    try:
        return tracker.monthly_summary(month)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/expenses")
def get_expenses(month: str = "", category: str = ""):
    """List expenses, optionally filtered by month and category."""
    try:
        return tracker.list_expenses(month, category)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/expenses", status_code=201)
def create_expense(expense: ExpenseInput):
    """Record an expense and return it with its generated ID."""
    try:
        return tracker.add_expense(expense.amount, expense.category, expense.expense_date, expense.description)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/expenses/{expense_id}")
def remove_expense(expense_id: int):
    """Delete an expense by ID, or return 404 if it does not exist."""
    result = tracker.delete_expense(expense_id)
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return result


@app.put("/api/expenses/{expense_id}")
def replace_expense(expense_id: int, expense: ExpenseUpdateInput):
    """Replace an expense by ID, or return 404 if it does not exist."""
    result = tracker.update_expense(
        expense_id, expense.amount, expense.category, expense.expense_date, expense.description
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return result


@app.put("/api/budgets")
def update_budget(budget: BudgetInput):
    """Create or replace a category budget for the specified month."""
    try:
        return tracker.set_budget(budget.month, budget.category, budget.amount)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error