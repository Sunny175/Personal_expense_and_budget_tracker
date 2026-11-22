from fastapi import FastAPI, HTTPException, Query, Security
from pydantic import BaseModel, field_validator

from tracker.core import tracker
from tracker.api.auth import require_owner


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
def get_summary(month: str = Query(...), owner: str = Security(require_owner, scopes=["read:expenses"])):
    """Return spending and category budget progress for the requested month."""
    try:
        return tracker.monthly_summary(month, owner=owner)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/api/expenses")
def get_expenses(month: str = "", category: str = "", owner: str = Security(require_owner, scopes=["read:expenses"])):
    """List expenses, optionally filtered by month and category."""
    try:
        return tracker.list_expenses(month, category, owner=owner)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/expenses", status_code=201)
def create_expense(expense: ExpenseInput, owner: str = Security(require_owner, scopes=["write:expenses"])):
    """Record an expense and return it with its generated ID."""
    try:
        return tracker.add_expense(expense.amount, expense.category, expense.expense_date, expense.description, owner=owner)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/api/expenses/{expense_id}")
def remove_expense(expense_id: int, owner: str = Security(require_owner, scopes=["write:expenses"])):
    """Delete an expense by ID, or return 404 if it does not exist."""
    result = tracker.delete_expense(expense_id, owner=owner)
    if not result["deleted"]:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return result


@app.put("/api/expenses/{expense_id}")
def replace_expense(expense_id: int, expense: ExpenseUpdateInput, owner: str = Security(require_owner, scopes=["write:expenses"])):
    """Replace an expense by ID, or return 404 if it does not exist."""
    result = tracker.update_expense(
        expense_id, expense.amount, expense.category, expense.expense_date, expense.description, owner=owner
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return result


@app.put("/api/budgets")
def update_budget(budget: BudgetInput, owner: str = Security(require_owner, scopes=["write:expenses"])):
    """Create or replace a category budget for the specified month."""
    try:
        return tracker.set_budget(budget.month, budget.category, budget.amount, owner=owner)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error