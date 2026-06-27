from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import Transaction, TransactionCreate, TransactionOut
from services.auth_service import get_current_user
from models.schemas import User

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.get("/", response_model=list[TransactionOut])
def get_transactions(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    return db.query(Transaction)\
             .filter(Transaction.user_id == current_user.id)\
             .order_by(Transaction.date.desc())\
             .all()

@router.post("/", response_model=TransactionOut)
def create_transaction(
    body:         TransactionCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    tx = Transaction(**body.model_dump(), user_id=current_user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.delete("/{tx_id}")
def delete_transaction(
    tx_id:        int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    tx = db.query(Transaction).filter(
        Transaction.id == tx_id,
        Transaction.user_id == current_user.id
    ).first()
    if not tx:
        raise HTTPException(404, "Transaction not found")
    db.delete(tx)
    db.commit()
    return {"deleted": tx_id}