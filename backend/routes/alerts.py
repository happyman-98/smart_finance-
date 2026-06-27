from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.schemas import Transaction
import os
from twilio.rest import Client   

router = APIRouter()

class AlertRequest(BaseModel):
    phone_number: str   # e.g. "+9779800000000"
    threshold:    float # alert if expense exceeds this

@router.post("/alerts/sms")
def send_sms_alert(request: AlertRequest, db: Session = Depends(get_db)):
    # Calculate current month total expense
    from datetime import datetime
    current_month = datetime.utcnow().strftime("%Y-%m")

    transactions = db.query(Transaction).filter(
        Transaction.type == "expense"
    ).all()

    monthly_expense = sum(
        t.amount for t in transactions
        if t.date.strftime("%Y-%m") == current_month
    )

    if monthly_expense < request.threshold:
        return {
            "sent":    False,
            "reason":  "Expense below threshold",
            "expense": monthly_expense
        }

    # Send via Twilio
    client = Client(
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN")
    )

    client.messages.create(
        body=f"⚠️ Finance Alert: Your expense this month is Rs.{monthly_expense:.2f}, exceeding your limit of Rs.{request.threshold:.2f}",
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        to=request.phone_number
    )

    return {
        "sent":            True,
        "monthly_expense": monthly_expense,
        "threshold":       request.threshold
    }