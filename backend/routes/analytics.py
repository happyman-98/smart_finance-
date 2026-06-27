from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import get_db
from models.schemas import Transaction, User
from services.auth_service import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary")
def get_summary(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    txs = db.query(Transaction)\
            .filter(Transaction.user_id == current_user.id)\
            .all()

    total_income  = sum(t.amount for t in txs if t.type == "income")
    total_expense = sum(t.amount for t in txs if t.type == "expense")
    net_balance   = total_income - total_expense

    # Spending by category
    by_category = {}
    for t in txs:
        if t.type == "expense":
            by_category[t.category] = by_category.get(t.category, 0) + t.amount

    # Monthly totals for chart (last 12 months)
    from datetime import datetime, timezone
    from collections import defaultdict
    monthly = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in txs:
        key = t.date.strftime("%b")
        monthly[key][t.type] += t.amount

    return {
        "net_balance":    round(net_balance, 2),
        "total_income":   round(total_income, 2),
        "total_expense":  round(total_expense, 2),
        "by_category":    by_category,
        "monthly":        dict(monthly),
        "savings_goal":   current_user.monthly_savings_goal,
        "monthly_income": current_user.monthly_income,
    }