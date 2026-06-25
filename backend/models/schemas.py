from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime
from database import Base

# ─── DB Tables ───────────────────────────────────────────

class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True, index=True)
    amount      = Column(Float, nullable=False)
    category    = Column(String)
    merchant    = Column(String)
    date        = Column(DateTime, default=datetime.utcnow)
    type        = Column(String)  
    description = Column(String, nullable=True)

class Goal(Base):
    __tablename__ = "goals"
    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String, nullable=False)
    target_amount  = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline       = Column(DateTime)
    created_at     = Column(DateTime, default=datetime.utcnow)

# ─── Pydantic (Request / Response) ───────────────────────

class TransactionCreate(BaseModel):
    amount:      float
    category:    str
    merchant:    str
    date:        datetime
    type:        str          # "income" or "expense"
    description: str | None = None

class TransactionOut(TransactionCreate):
    id: int
    class Config:
        from_attributes = True

class GoalCreate(BaseModel):
    title:         str
    target_amount: float
    deadline:      datetime

class GoalOut(GoalCreate):
    id:             int
    current_amount: float
    created_at:     datetime
    class Config:
        from_attributes = True