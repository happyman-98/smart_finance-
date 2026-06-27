from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import User, UserCreate, UserOut, LoginRequest, TokenOut
from services.auth_service import hash_password, verify_password, create_token
from services.auth_service import get_current_user as get_current_user_import

router = APIRouter()
class UserUpdate(BaseModel):
    monthly_income:       float | None = None
    monthly_savings_goal: float | None = None
 

@router.post("/auth/register", response_model=TokenOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name     = data.name,
        email    = data.email,
        password = hash_password(data.password),   
        phone    = data.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return {"access_token": token, "user": user}


@router.post("/auth/login", response_model=TokenOut)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user.id)
    return {"access_token": token, "user": user}



@router.put("/auth/me", response_model=UserOut)
def update_me(
    data:         UserUpdate,
    db:           Session                        = Depends(get_db),
    current_user: User                           = Depends(get_current_user_import)
):
    if data.monthly_income is not None:
        current_user.monthly_income = data.monthly_income
    if data.monthly_savings_goal is not None:
        current_user.monthly_savings_goal = data.monthly_savings_goal
    db.commit()
    db.refresh(current_user)
    return current_user