from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models import User
from schemas import FoodCreate, FoodUpdate, FoodOut
from repositories.food_repository import FoodRepository

class FoodService:
    def __init__(self, db: Session):
        self.repo = FoodRepository(db)

    def list_foods(self, search: Optional[str] = None, category: Optional[str] = None) -> List[FoodOut]:
        foods = self.repo.get_all(search=search, category=category)
        return [FoodOut.model_validate(f) for f in foods]

    def get_food(self, food_id: int) -> FoodOut:
        food = self.repo.get_by_id(food_id)
        if not food:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")
        return FoodOut.model_validate(food)

    def create_food(self, food_data: FoodCreate, current_user: User) -> FoodOut:
        if current_user.role == "admin":
            food_data.is_verified = True
        else:
            food_data.is_verified = False

        food = self.repo.create(food_data, creator_id=current_user.id)
        return FoodOut.model_validate(food)

    def update_food(self, food_id: int, update_data: FoodUpdate, current_user: User) -> FoodOut:
        food = self.repo.get_by_id(food_id)
        if not food:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

        if current_user.role != "admin" and food.created_by_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на редактирование")

        updated = self.repo.update(food, update_data)
        return FoodOut.model_validate(updated)

    def delete_food(self, food_id: int, current_user: User) -> None:
        food = self.repo.get_by_id(food_id)
        if not food:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

        if current_user.role != "admin" and food.created_by_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав на удаление")

        self.repo.delete(food)
