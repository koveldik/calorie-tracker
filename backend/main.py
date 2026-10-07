import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models import User, UserRole, FoodItem
from auth import get_password_hash
from routers import auth, foods, meals

app = FastAPI(
    title="Calorie Tracker API",
    description="Информационная система учета питания и подсчета калорий",
    version="1.0.0"
)

# Разрешаем CORS для обращения из любого UI / Docker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(foods.router)
app.include_router(meals.router)


@app.on_event("startup")
def startup_init():
    """Подключение к базе данных с повторными попытками и наполнение данными"""
    # Ждем готовности базы данных до 10 секунд
    connected = False
    for attempt in range(1, 11):
        try:
            Base.metadata.create_all(bind=engine)
            connected = True
            break
        except Exception as e:
            print(f"[Попытка {attempt}/10] Ожидание базы данных: {e}")
            time.sleep(1)

    if not connected:
        print("[ОШИБКА] Не удалось подключиться к базе данных.")
        return

    # Наполнение тестовыми данными
    db = SessionLocal()
    try:
        # 1. Создание тестового администратора, если его нет
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@calorie.local",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                daily_calorie_target=2500
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # 2. Создание тестового клиента, если его нет
        client = db.query(User).filter(User.username == "client").first()
        if not client:
            client = User(
                username="client",
                email="client@calorie.local",
                hashed_password=get_password_hash("client123"),
                role=UserRole.CLIENT,
                daily_calorie_target=2100
            )
            db.add(client)
            db.commit()
            db.refresh(client)

        # 3. Наполнение базовым справочником продуктов
        if db.query(FoodItem).count() == 0:
            initial_foods = [
                FoodItem(name="Куриное филе (грудка вареная)", calories=165, proteins=31.0, fats=3.6, carbs=0.0, category="Мясо и птица", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Гречневая каша (на воде)", calories=101, proteins=3.6, fats=0.8, carbs=21.3, category="Крупы", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Овсяная каша", calories=88, proteins=3.0, fats=1.7, carbs=15.0, category="Крупы", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Яйцо куриное вареное", calories=155, proteins=12.6, fats=10.6, carbs=1.1, category="Яйца", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Творог 5%", calories=121, proteins=17.0, fats=5.0, carbs=1.8, category="Молочные продукты", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Банан свежий", calories=89, proteins=1.1, fats=0.3, carbs=22.8, category="Фрукты", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Яблоко зеленое", calories=52, proteins=0.3, fats=0.2, carbs=13.8, category="Фрукты", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Рис басмати вареный", calories=130, proteins=2.7, fats=0.3, carbs=28.2, category="Крупы", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Лосось на пару", calories=182, proteins=20.0, fats=11.0, carbs=0.0, category="Рыба", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Огурец свежий", calories=15, proteins=0.7, fats=0.1, carbs=3.6, category="Овощи", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Помидор свежий", calories=18, proteins=0.9, fats=0.2, carbs=3.9, category="Овощи", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Арахисовая паста", calories=588, proteins=25.0, fats=50.0, carbs=20.0, category="Орехи и снеки", is_verified=True, created_by_id=admin.id),
                FoodItem(name="Протеин сывороточный (порция)", calories=120, proteins=24.0, fats=1.5, carbs=3.0, category="Спортивное питание", is_verified=True, created_by_id=admin.id),
            ]
            db.add_all(initial_foods)
            db.commit()
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Calorie Tracker API",
        "docs": "/docs",
        "author": "Ivan Kartavcev"
    }
