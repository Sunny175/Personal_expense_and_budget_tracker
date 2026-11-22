import re
from datetime import date
from decimal import Decimal, InvalidOperation

from tracker.storage import repository


def parse_amount(amount: str) -> int:
    """Validate a positive decimal amount and return it in integer cents."""
    try:
        value = Decimal(amount)
        exponent = value.as_tuple().exponent
        if (
            not value.is_finite()
            or not isinstance(exponent, int)
            or value <= 0
            or value > 90_000_000_000_000
            or exponent < -2
        ):
            raise ValueError
        cents = value * 100
        return int(cents)
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be positive with at most two decimal places.") from None


def format_amount(cents: int) -> str:
    """Format signed integer cents as a two-decimal amount string."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def validate_month(month: str) -> str:
    """Return a valid YYYY-MM month or raise ValueError."""
    if not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month) or month.startswith("0000-"):
        raise ValueError("Month must be in YYYY-MM format.")
    return month


def validate_category(category: str) -> str:
    """Trim and case-fold a nonempty category or raise ValueError."""
    category = category.strip()
    if not category:
        raise ValueError("Category cannot be empty.")
    return category.casefold()


def validate_expense_date(expense_date: str) -> str:
    """Return a valid YYYY-MM-DD date or raise ValueError."""
    try:
        if date.fromisoformat(expense_date).isoformat() != expense_date:
            raise ValueError
    except ValueError:
        raise ValueError("Expense date must be in YYYY-MM-DD format.") from None
    return expense_date


def add_expense(amount: str, category: str, expense_date: str = "", description: str = "") -> dict:
    """Record an expense. Amount is a decimal string; date is YYYY-MM-DD (default: today)."""
    cents = parse_amount(amount)
    category = validate_category(category)
    if expense_date:
        expense_date = validate_expense_date(expense_date)
    else:
        expense_date = date.today().isoformat()
    expense_id = repository.insert_expense(expense_date, category, cents, description.strip())
    return {"id": expense_id, "date": expense_date, "category": category,
            "amount": format_amount(cents), "description": description.strip()}


def list_expenses(month: str = "", category: str = "") -> list[dict]:
    """List expenses, optionally filtered by YYYY-MM and category."""
    if month:
        month = validate_month(month)
    if category:
        category = validate_category(category)
    rows = repository.get_expenses(month, category)
    return [{"id": row["id"], "date": row["expense_date"], "category": row["category"],
             "amount": format_amount(row["amount_cents"]), "description": row["description"]}
            for row in rows]


def delete_expense(expense_id: int) -> dict:
    """Delete an expense by its ID."""
    return {"id": expense_id, "deleted": repository.remove_expense(expense_id)}


def update_expense(expense_id: int, amount: str, category: str, expense_date: str, description: str = "") -> dict | None:
    """Replace an existing expense, or return None if its ID does not exist."""
    cents = parse_amount(amount)
    category = validate_category(category)
    expense_date = validate_expense_date(expense_date)
    description = description.strip()
    updated = repository.replace_expense(expense_id, expense_date, category, cents, description)
    if not updated:
        return None
    return {"id": expense_id, "date": expense_date, "category": category,
            "amount": format_amount(cents), "description": description}


def set_budget(month: str, category: str, amount: str) -> dict:
    """Set or replace a category budget for a month (YYYY-MM)."""
    month = validate_month(month)
    category = validate_category(category)
    cents = parse_amount(amount)
    repository.upsert_budget(month, category, cents)
    return {"month": month, "category": category, "amount": format_amount(cents)}


def monthly_summary(month: str) -> dict:
    """Summarize spending and category budgets for a month (YYYY-MM)."""
    month = validate_month(month)
    spending, budgets = repository.get_monthly_totals(month)
    categories = {}
    for row in budgets:
        categories[row["category"].lower()] = {"category": row["category"], "budget": row["amount_cents"], "spent": 0}
    for row in spending:
        entry = categories.setdefault(row["category"].lower(), {"category": row["category"], "budget": None, "spent": 0})
        entry["spent"] = row["total"]
    result = []
    for entry in sorted(categories.values(), key=lambda item: item["category"].lower()):
        budget = entry["budget"]
        spent = entry["spent"]
        result.append({"category": entry["category"], "spent": format_amount(spent),
                       "budget": format_amount(budget) if budget is not None else None,
                       "remaining": format_amount(budget - spent) if budget is not None else None,
                       "over_budget": budget is not None and spent > budget})
    return {"month": month, "total_spent": format_amount(sum(row["total"] for row in spending)), "categories": result}

