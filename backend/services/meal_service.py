from datetime import date
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import User
from schemas import MealEntryCreate, MealEntryUpdate, DailyDiaryResponse, MealEntryOut
from repositories.meal_repository import MealRepository
from repositories.food_repository import FoodRepository

class MealService:
    def __init__(self, db: Session):
        self.meal_repo = MealRepository(db)
        self.food_repo = FoodRepository(db)

    @staticmethod
    def _calculate_nutrients(food, weight: float) -> dict:
        factor = weight / 100.0
        return {
            "calories": round(food.calories * factor, 1),
            "protein": round(food.protein * factor, 1),
            "fat": round(food.fat * factor, 1),
            "carbs": round(food.carbs * factor, 1),
        }

    def get_user_diary(self, user_id: int, diary_date: date) -> DailyDiaryResponse:
        meals = self.meal_repo.get_by_user_and_date(user_id=user_id, target_date=diary_date)
        meal_outs = [MealEntryOut.model_validate(m) for m in meals]

        return DailyDiaryResponse(
            date=diary_date,
            entries=meal_outs,
            total_calories=round(sum(m.calories for m in meal_outs), 1),
            total_protein=round(sum(m.protein for m in meal_outs), 1),
            total_fat=round(sum(m.fat for m in meal_outs), 1),
            total_carbs=round(sum(m.carbs for m in meal_outs), 1)
        )

    def add_meal(self, user_id: int, meal_data: MealEntryCreate) -> MealEntryOut:
        food = self.food_repo.get_by_id(meal_data.food_id)
        if not food:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

        nutrients = self._calculate_nutrients(food, meal_data.weight_grams)
        created_meal = self.meal_repo.create(user_id, meal_data, nutrients)
        return MealEntryOut.model_validate(created_meal)

    def update_meal(self, meal_id: int, update_data: MealEntryUpdate, current_user: User) -> MealEntryOut:
        meal = self.meal_repo.get_by_id(meal_id)
        if not meal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")

        if current_user.role != "admin" and meal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

        update_dict = update_data.model_dump(exclude_unset=True)
        if "food_id" in update_dict or "weight_grams" in update_dict:
            target_food_id = update_dict.get("food_id", meal.food_id)
            target_weight = update_dict.get("weight_grams", meal.weight_grams)
            food = self.food_repo.get_by_id(target_food_id)
            if not food:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")
            update_dict.update(self._calculate_nutrients(food, target_weight))

        updated_meal = self.meal_repo.update(meal, update_dict)
        return MealEntryOut.model_validate(updated_meal)

    def delete_meal(self, meal_id: int, current_user: User) -> None:
        meal = self.meal_repo.get_by_id(meal_id)
        if not meal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")

        if current_user.role != "admin" and meal.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа")

        self.meal_repo.delete(meal)
