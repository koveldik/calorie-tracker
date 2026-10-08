from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from database import get_db
from schemas import FoodCreate, FoodUpdate, FoodOut
from auth import get_current_user
from models import User
from services.food_service import FoodService

router = APIRouter(prefix="/foods", tags=["Продукты"])

@router.get("/", response_model=List[FoodOut])
def list_foods(search: Optional[str] = Query(None), category: Optional[str] = Query(None), db: Session = Depends(get_db)):
    return FoodService(db).list_foods(search, category)

@router.get("/{food_id}", response_model=FoodOut)
def get_food(food_id: int, db: Session = Depends(get_db)):
    return FoodService(db).get_food(food_id)

@router.post("/", response_model=FoodOut, status_code=status.HTTP_201_CREATED)
def create_food(food: FoodCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return FoodService(db).create_food(food, current_user)

@router.put("/{food_id}", response_model=FoodOut)
def update_food(food_id: int, food_update: FoodUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return FoodService(db).update_food(food_id, food_update, current_user)

@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(food_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    FoodService(db).delete_food(food_id, current_user)
