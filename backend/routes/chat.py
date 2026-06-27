# routes/chat.py
# Add to main.py: app.include_router(chat.router, prefix="/api")

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from models.schemas import Transaction, User
from services.auth_service import get_current_user
from services.chat_service import FinanceBot

router = APIRouter(prefix="/chat", tags=["chat"])

# ── In-memory session store (one FinanceBot per user) ────────────────────────
# For production swap this for Redis + pickle / a proper session backend.
_sessions: dict[int, FinanceBot] = {}

def _get_bot(user_id: int) -> FinanceBot:
    if user_id not in _sessions:
        _sessions[user_id] = FinanceBot()
    return _sessions[user_id]


class ChatRequest(BaseModel):
    message: str


# ── Build live context from DB (same logic as analytics/summary) ─────────────
def _build_ctx(user: User, db: Session) -> dict:
    txs          = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    total_income  = sum(t.amount for t in txs if t.type == "income")
    total_expense = sum(t.amount for t in txs if t.type == "expense")
    by_category: dict[str, float] = {}
    for t in txs:
        if t.type == "expense":
            by_category[t.category] = by_category.get(t.category, 0) + t.amount
    return {
        "name":                 user.name,
        "net_balance":          round(total_income - total_expense, 2),
        "total_income":         round(total_income,  2),
        "total_expense":        round(total_expense, 2),
        "monthly_income":       user.monthly_income,
        "monthly_savings_goal": user.monthly_savings_goal,
        "by_category":          by_category,
    }


# ── Stream endpoint ───────────────────────────────────────────────────────────
@router.post("/stream")
def chat_stream(
    body:         ChatRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    bot = _get_bot(current_user.id)
    ctx = _build_ctx(current_user, db)

    def generate():
        for chunk in bot.stream(body.message, ctx):
            # Server-Sent Events format so the browser can read chunks live
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Reset endpoint ────────────────────────────────────────────────────────────
@router.post("/reset")
def chat_reset(current_user: User = Depends(get_current_user)):
    if current_user.id in _sessions:
        _sessions[current_user.id].reset()
    return {"reset": True}