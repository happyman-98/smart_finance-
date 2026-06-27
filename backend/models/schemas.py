from sqlalchemy import Column, ForeignKey, Integer, Float, String, DateTime
from sqlalchemy.orm import relationship
from pydantic import BaseModel,EmailStr
from datetime import datetime, timezone
from models.database import Base

# ─── DB Tables ───────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=False, index=True)
    password   = Column(String, nullable=False)   # hashed, never plain text
    phone      = Column(String, nullable=True)     # for SMS alerts
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships — one user has many transactions and goals
    transactions = relationship("Transaction", back_populates="owner")
    goals        = relationship("Goal", back_populates="owner")

class Transaction(Base):
    __tablename__ = "transactions"
    id          = Column(Integer, primary_key=True, index=True)
    amount      = Column(Float, nullable=False)
    category    = Column(String)
    merchant    = Column(String)
    date        = Column(DateTime, default=datetime.utcnow)
    type        = Column(String)  
    description = Column(String, nullable=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner       = relationship("User", back_populates="transactions")

class Goal(Base):
    __tablename__ = "goals"
    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String, nullable=False)
    target_amount  = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    deadline       = Column(DateTime)
    created_at     = Column(DateTime, default=datetime.utcnow)
    user_id        = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner          = relationship("User", back_populates="goals")

# ─── Pydantic (Request / Response) ───────────────────────
class UserCreate(BaseModel):
    name:     str
    email:    EmailStr
    password: str
    phone:    str | None = None

class UserOut(BaseModel):
    id:         int
    name:       str
    email:      str
    phone:      str | None
    created_at: datetime
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email:    EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut

class TransactionCreate(BaseModel):
    amount:      float
    category:    str
    merchant:    str
    date:        datetime
    type:        str          # "income" or "expense"
    description: str | None = None

class TransactionOut(TransactionCreate):
    id: int
    user_id: int  
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
    user_id: int  
    class Config:
        from_attributes = True