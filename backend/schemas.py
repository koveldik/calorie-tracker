from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models import UserRole, MealType


# --- Схемы пользователя и авторизации ---

class UserBase(BaseModel):
    username: str
    email: str
    daily_calorie_target: Optional[int] = 2000


class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.CLIENT


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: int
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


# --- Схемы продукта (Бизнес-сущность 1) ---

class FoodItemBase(BaseModel):
    name: str
    calories: float = Field(..., gt=0, description="Калории на 100 грамм")
    proteins: float = Field(0.0, ge=0, description="Белки на 100 грамм")
    fats: float = Field(0.0, ge=0, description="Жиры на 100 грамм")
    carbs: float = Field(0.0, ge=0, description="Углеводы на 100 грамм")
    category: Optional[str] = "Общее"


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[float] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbs: Optional[float] = None
    category: Optional[str] = None
    is_verified: Optional[bool] = None


class FoodItemOut(FoodItemBase):
    id: int
    is_verified: bool
    created_by_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Схемы записи приёма пищи (Бизнес-сущность 2) ---

class MealEntryBase(BaseModel):
    food_id: int
    meal_type: MealType = MealType.BREAKFAST
    weight_grams: float = Field(..., gt=0, description="Вес порции в граммах")
    note: Optional[str] = None
    consumed_at: Optional[datetime] = None


class MealEntryCreate(MealEntryBase):
    pass


class MealEntryUpdate(BaseModel):
    food_id: Optional[int] = None
    meal_type: Optional[MealType] = None
    weight_grams: Optional[float] = None
    note: Optional[str] = None
    consumed_at: Optional[datetime] = None


class MealEntryOut(BaseModel):
    id: int
    user_id: int
    food_id: int
    meal_type: MealType
    weight_grams: float
    note: Optional[str]
    consumed_at: datetime
    created_at: datetime
    food: FoodItemOut

    # Вычисляемые поля для порции
    portion_calories: float
    portion_proteins: float
    portion_fats: float
    portion_carbs: float

    class Config:
        from_attributes = True


# --- Схема дневной статистики ---

class DailySummary(BaseModel):
    date: str
    target_calories: int
    consumed_calories: float
    remaining_calories: float
    total_proteins: float
    total_fats: float
    total_carbs: float
    entries_count: int
