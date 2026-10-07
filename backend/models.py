import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, enum.Enum):
    CLIENT = "client"
    ADMIN = "admin"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    daily_calorie_target = Column(Integer, default=2000)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    created_foods = relationship("FoodItem", back_populates="created_by", cascade="all, delete-orphan")
    meal_entries = relationship("MealEntry", back_populates="user", cascade="all, delete-orphan")


class FoodItem(Base):
    """
    Бизнес-сущность 1: Продукт питания / Блюдо
    Хранит калорийность и БЖУ в расчете на 100 грамм продукта.
    """
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), index=True, nullable=False)
    calories = Column(Float, nullable=False)   # ккал на 100 г
    proteins = Column(Float, default=0.0)      # белки на 100 г
    fats = Column(Float, default=0.0)          # жиры на 100 г
    carbs = Column(Float, default=0.0)         # углеводы на 100 г
    category = Column(String(50), default="Общее") # Категория (Мясо, Молочные, Крупы и т.д.)
    is_verified = Column(Boolean, default=False) # Проверено администратором
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    created_by = relationship("User", back_populates="created_foods")
    meal_entries = relationship("MealEntry", back_populates="food", cascade="all, delete-orphan")


class MealEntry(Base):
    """
    Бизнес-сущность 2: Запись в дневнике приёма пищи
    Фиксирует конкретный приём пищи пользователя, граммовку и время.
    """
    __tablename__ = "meal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("food_items.id", ondelete="RESTRICT"), nullable=False)
    meal_type = Column(Enum(MealType), default=MealType.BREAKFAST, nullable=False)
    weight_grams = Column(Float, nullable=False)
    note = Column(String(200), nullable=True)
    consumed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="meal_entries")
    food = relationship("FoodItem", back_populates="meal_entries")
