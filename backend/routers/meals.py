from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from database import get_db
from models import MealEntry, FoodItem, User, UserRole, MealType
from schemas import MealEntryCreate, MealEntryUpdate, MealEntryOut, DailySummary
from auth import get_current_user, require_admin

router = APIRouter(prefix="/api/meals", tags=["Дневник питания (CRUD 2)"])


def _calculate_portion_macros(entry: MealEntry) -> dict:
    """Вспомогательная функция для расчета питательной ценности порции"""
    ratio = entry.weight_grams / 100.0
    food = entry.food
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "food_id": entry.food_id,
        "meal_type": entry.meal_type,
        "weight_grams": entry.weight_grams,
        "note": entry.note,
        "consumed_at": entry.consumed_at,
        "created_at": entry.created_at,
        "food": food,
        "portion_calories": round(food.calories * ratio, 1),
        "portion_proteins": round(food.proteins * ratio, 1),
        "portion_fats": round(food.fats * ratio, 1),
        "portion_carbs": round(food.carbs * ratio, 1),
    }


@router.post("/", response_model=MealEntryOut, status_code=status.HTTP_201_CREATED)
def create_meal_entry(
    meal_in: MealEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [CREATE] Добавление записи о приеме пищи в дневник пользователя.
    """
    food = db.query(FoodItem).filter(FoodItem.id == meal_in.food_id).first()
    if not food:
        raise HTTPException(status_code=404, detail="Выбранный продукт не найден")

    consumed_time = meal_in.consumed_at or datetime.utcnow()

    entry = MealEntry(
        user_id=current_user.id,
        food_id=meal_in.food_id,
        meal_type=meal_in.meal_type,
        weight_grams=meal_in.weight_grams,
        note=meal_in.note,
        consumed_at=consumed_time
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Загружаем связанный продукт
    entry.food = food
    return _calculate_portion_macros(entry)


@router.get("/", response_model=List[MealEntryOut])
def list_my_meals(
    target_date: Optional[date] = Query(None, description="Дата в формате YYYY-MM-DD"),
    meal_type: Optional[MealType] = Query(None, description="Фильтр по типу приема пищи"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [READ] Список приемов пищи текущего пользователя за определенную дату (по умолчанию — сегодня).
    """
    query_date = target_date or date.today()
    start_dt = datetime.combine(query_date, datetime.min.time())
    end_dt = datetime.combine(query_date, datetime.max.time())

    query = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.food))
        .filter(MealEntry.user_id == current_user.id)
        .filter(MealEntry.consumed_at >= start_dt, MealEntry.consumed_at <= end_dt)
    )

    if meal_type:
        query = query.filter(MealEntry.meal_type == meal_type)

    entries = query.order_by(MealEntry.consumed_at.asc()).all()
    return [_calculate_portion_macros(e) for e in entries]


@router.get("/summary", response_model=DailySummary)
def get_daily_summary(
    target_date: Optional[date] = Query(None, description="Дата в формате YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [READ] Сводная статистика за день: калории, БЖУ, прогресс выполнения суточной нормы.
    """
    query_date = target_date or date.today()
    start_dt = datetime.combine(query_date, datetime.min.time())
    end_dt = datetime.combine(query_date, datetime.max.time())

    entries = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.food))
        .filter(MealEntry.user_id == current_user.id)
        .filter(MealEntry.consumed_at >= start_dt, MealEntry.consumed_at <= end_dt)
        .all()
    )

    total_cal = 0.0
    total_prot = 0.0
    total_fats = 0.0
    total_carbs = 0.0

    for e in entries:
        ratio = e.weight_grams / 100.0
        total_cal += e.food.calories * ratio
        total_prot += e.food.proteins * ratio
        total_fats += e.food.fats * ratio
        total_carbs += e.food.carbs * ratio

    target = current_user.daily_calorie_target or 2000
    remaining = max(0.0, target - total_cal)

    return DailySummary(
        date=query_date.isoformat(),
        target_calories=target,
        consumed_calories=round(total_cal, 1),
        remaining_calories=round(remaining, 1),
        total_proteins=round(total_prot, 1),
        total_fats=round(total_fats, 1),
        total_carbs=round(total_carbs, 1),
        entries_count=len(entries)
    )


@router.get("/{entry_id}", response_model=MealEntryOut)
def get_meal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """[READ] Получение конкретной записи дневника по ID"""
    entry = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.food))
        .filter(MealEntry.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись приёма пищи не найдена")

    if current_user.role != UserRole.ADMIN and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Доступ к чужой записи запрещен")

    return _calculate_portion_macros(entry)


@router.put("/{entry_id}", response_model=MealEntryOut)
def update_meal_entry(
    entry_id: int,
    meal_update: MealEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [UPDATE] Редактирование записи в дневнике (вес порции, время, комментарий, тип приема).
    """
    entry = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.food))
        .filter(MealEntry.id == entry_id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Запись приёма пищи не найдена")

    if current_user.role != UserRole.ADMIN and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы можете редактировать только свои записи")

    update_data = meal_update.model_dump(exclude_unset=True)

    if "food_id" in update_data and update_data["food_id"] is not None:
        new_food = db.query(FoodItem).filter(FoodItem.id == update_data["food_id"]).first()
        if not new_food:
            raise HTTPException(status_code=404, detail="Новый продукт не найден")
        entry.food = new_food

    for key, value in update_data.items():
        setattr(entry, key, value)

    db.commit()
    db.refresh(entry)
    return _calculate_portion_macros(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    [DELETE] Удаление записи из дневника питания.
    - Client может удалять только свои записи.
    - Admin может удалять любые записи.
    """
    entry = db.query(MealEntry).filter(MealEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Запись приёма пищи не найдена")

    if current_user.role != UserRole.ADMIN and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Вы можете удалять только свои записи")

    db.delete(entry)
    db.commit()
    return None


@router.get("/admin/all", response_model=List[MealEntryOut])
def admin_list_all_meals(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    [ADMIN ONLY] Просмотр всех записей дневника питания всех пользователей платформы.
    """
    entries = (
        db.query(MealEntry)
        .options(joinedload(MealEntry.food))
        .order_by(MealEntry.consumed_at.desc())
        .limit(100)
        .all()
    )
    return [_calculate_portion_macros(e) for e in entries]
