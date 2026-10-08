from typing import List, Optional
from sqlalchemy.orm import Session
from models import FoodItem
from schemas import FoodCreate, FoodUpdate

class FoodRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, search: Optional[str] = None, category: Optional[str] = None) -> List[FoodItem]:
        query = self.db.query(FoodItem)
        if search:
            query = query.filter(FoodItem.name.ilike(f"%{search}%"))
        if category:
            query = query.filter(FoodItem.category == category)
        return query.order_by(FoodItem.name).all()

    def get_by_id(self, food_id: int) -> Optional[FoodItem]:
        return self.db.query(FoodItem).filter(FoodItem.id == food_id).first()

    def create(self, food_data: FoodCreate, creator_id: Optional[int] = None) -> FoodItem:
        food = FoodItem(
            name=food_data.name,
            category=food_data.category,
            calories=food_data.calories,
            protein=food_data.protein,
            fat=food_data.fat,
            carbs=food_data.carbs,
            is_verified=food_data.is_verified,
            created_by_id=creator_id
        )
        self.db.add(food)
        self.db.commit()
        self.db.refresh(food)
        return food

    def update(self, food: FoodItem, update_data: FoodUpdate) -> FoodItem:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(food, key, value)
        self.db.commit()
        self.db.refresh(food)
        return food

    def delete(self, food: FoodItem) -> None:
        self.db.delete(food)
        self.db.commit()
