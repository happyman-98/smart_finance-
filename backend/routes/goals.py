from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import Goal, GoalCreate, GoalOut
from services.auth_service import get_current_user
from models.schemas import User

router = APIRouter(prefix="/goals", tags=["goals"])

@router.get("/", response_model=list[GoalOut])
def get_goals(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    return db.query(Goal)\
             .filter(Goal.user_id == current_user.id)\
             .all()

@router.post("/", response_model=GoalOut)
def create_goal(
    body:         GoalCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    goal = Goal(**body.model_dump(), user_id=current_user.id)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal

@router.patch("/{goal_id}/deposit", response_model=GoalOut)
def add_to_goal(
    goal_id:      int,
    amount:       float,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    goal = db.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(404, "Goal not found")
    goal.current_amount += amount
    db.commit()
    db.refresh(goal)
    return goal