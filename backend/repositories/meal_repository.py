from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from models import MealEntry
from schemas import MealEntryCreate, MealEntryUpdate

class MealRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_and_date(self, user_id: int, target_date: date) -> List[MealEntry]:
        return self.db.query(MealEntry).filter(
            MealEntry.user_id == user_id,
            MealEntry.date == target_date
        ).all()

    def get_all(self, target_date: Optional[date] = None) -> List[MealEntry]:
        query = self.db.query(MealEntry)
        if target_date:
            query = query.filter(MealEntry.date == target_date)
        return query.all()

    def get_by_id(self, meal_id: int) -> Optional[MealEntry]:
        return self.db.query(MealEntry).filter(MealEntry.id == meal_id).first()

    def create(self, user_id: int, meal_data: MealEntryCreate, calculated: dict) -> MealEntry:
        meal = MealEntry(
            user_id=user_id,
            food_id=meal_data.food_id,
            meal_type=meal_data.meal_type,
            weight_grams=meal_data.weight_grams,
            date=meal_data.date,
            calories=calculated["calories"],
            protein=calculated["protein"],
            fat=calculated["fat"],
            carbs=calculated["carbs"]
        )
        self.db.add(meal)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def update(self, meal: MealEntry, update_dict: dict) -> MealEntry:
        for key, value in update_dict.items():
            setattr(meal, key, value)
        self.db.commit()
        self.db.refresh(meal)
        return meal

    def delete(self, meal: MealEntry) -> None:
        self.db.delete(meal)
        self.db.commit()
