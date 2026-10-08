from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import MealEntryCreate, MealEntryUpdate, MealEntryOut, DailyDiaryResponse
from auth import get_current_user
from models import User
from services.meal_service import MealService

router = APIRouter(prefix="/meals", tags=["Дневник питания"])

@router.get("/daily", response_model=DailyDiaryResponse)
def get_daily_diary(diary_date: Optional[date] = Query(default=None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return MealService(db).get_user_diary(current_user.id, diary_date or date.today())

@router.post("/", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
def add_meal(meal: MealEntryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return MealService(db).add_meal(current_user.id, meal)

@router.put("/{meal_id}", response_model=MealEntryOut)
def update_meal(meal_id: int, meal_update: MealEntryUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return MealService(db).update_meal(meal_id, meal_update, current_user)

@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(meal_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    MealService(db).delete_meal(meal_id, current_user)
