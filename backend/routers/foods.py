from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import FoodItem, User, UserRole, MealEntry
from schemas import FoodItemCreate, FoodItemUpdate, FoodItemOut
from auth import get_current_user, require_admin

router = APIRouter(prefix="/api/foods", tags=["Продукты (CRUD 1)"])


@router.post("/", response_model=FoodItemOut, status_code=status.HTTP_201_CREATED)
def create_food(
    food_in: FoodItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [CREATE] Добавление нового продукта.
    - Для Admin: создается проверенный продукт (is_verified=True).
    - Для Client: создается пользовательский продукт (is_verified=False).
    """
    is_verified = (current_user.role == UserRole.ADMIN)

    food = FoodItem(
        name=food_in.name.strip(),
        calories=food_in.calories,
        proteins=food_in.proteins,
        fats=food_in.fats,
        carbs=food_in.carbs,
        category=food_in.category or "Общее",
        is_verified=is_verified,
        created_by_id=current_user.id
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


@router.get("/", response_model=List[FoodItemOut])
def list_foods(
    q: Optional[str] = Query(None, description="Поиск по названию"),
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    verified_only: Optional[bool] = Query(False, description="Только проверенные продукты"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [READ] Список продуктов с возможностью поиска и фильтрации.
    """
    query = db.query(FoodItem)
    if q:
        query = query.filter(FoodItem.name.ilike(f"%{q}%"))
    if category and category != "Все":
        query = query.filter(FoodItem.category == category)
    if verified_only:
        query = query.filter(FoodItem.is_verified == True)

    return query.order_by(FoodItem.name.asc()).all()


@router.get("/categories", response_model=List[str])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[READ] Получение уникального списка категорий продуктов"""
    categories = db.query(FoodItem.category).distinct().all()
    result = [cat[0] for cat in categories if cat[0]]
    if "Общее" not in result:
        result.insert(0, "Общее")
    return sorted(result)


@router.get("/{food_id}", response_model=FoodItemOut)
def get_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[READ] Получение детальной информации о продукте по ID"""
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return food


@router.put("/{food_id}", response_model=FoodItemOut)
def update_food(
    food_id: int,
    food_update: FoodItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [UPDATE] Обновление продукта.
    - Admin: может редактировать любой продукт и менять статус верификации.
    - Client: может редактировать только свой не верифицированный продукт.
    """
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    # Проверка прав доступа
    if current_user.role != UserRole.ADMIN:
        if food.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы не можете редактировать чужие продукты"
            )
        if food.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Проверенные администратором продукты нельзя изменять"
            )

    update_data = food_update.model_dump(exclude_unset=True)

    # Клиент не может сам себе поставить is_verified=True
    if current_user.role != UserRole.ADMIN and "is_verified" in update_data:
        del update_data["is_verified"]

    for key, value in update_data.items():
        setattr(food, key, value)

    db.commit()
    db.refresh(food)
    return food


@router.delete("/{food_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_food(
    food_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [DELETE] Удаление продукта.
    - Admin: может удалить любой продукт.
    - Client: может удалить только свой созданный продукт.
    """
    food = db.query(FoodItem).filter(FoodItem.id == food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    if current_user.role != UserRole.ADMIN:
        if food.created_by_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Вы можете удалять только созданные вами продукты"
            )

    # Проверяем, используется ли продукт в записях приемов пищи
    used_in_meals = db.query(MealEntry).filter(MealEntry.food_id == food_id).count()
    if used_in_meals > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Невозможно удалить продукт: он используется в {used_in_meals} записях дневника питания"
        )

    db.delete(food)
    db.commit()
    return None
