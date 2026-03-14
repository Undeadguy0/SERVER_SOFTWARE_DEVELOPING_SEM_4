from fastapi import FastAPI, HTTPException, Header, Request, Response, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, Annotated
from pydantic import ValidationError, Field
import time
from datetime import datetime, timezone

from models import User, UserAge, Feedback, UserCreate
from auth import router as auth_router, get_current_user_from_cookie

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}

@app.get("/html")
def get_html():
    return FileResponse("index.html")

@app.post("/calculate")
def calculate(num1: int, num2: int):
    result = num1 + num2
    return {"result": result}

user = User(
    name="Ваше Имя Фамилия",
    id=1
)

@app.get("/users")
def get_user():
    return user

@app.post("/user")
def check_user(user: UserAge):
    is_adult = user.age >= 18
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }

feedbacks = []
@app.post("/feedback")
def create_feedback(feedback: Feedback):
    feedbacks.append(feedback)
    return {"message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."}

@app.get("/feedback")
def get_feedbacks():
    return feedbacks


# --- НОВЫЕ ЭНДПОИНТЫ ДЛЯ КОНТРОЛЬНОЙ №2 ---

# Задание 3.1
@app.post("/create_user", response_model=UserCreate)
async def create_user(user_data: UserCreate):
    """
    Принимает данные пользователя, валидирует их и возвращает обратно.
    """
    # Здесь можно добавить логику сохранения в БД, но по заданию просто возвращаем
    print(f"Получен пользователь: {user_data}") # Для демонстрации
    return user_data


# Задание 3.2
# "База данных" товаров
sample_products = [
    {"product_id": 123, "name": "Smartphone", "category": "Electronics", "price": 599.99},
    {"product_id": 456, "name": "Phone Case", "category": "Accessories", "price": 19.99},
    {"product_id": 789, "name": "Iphone", "category": "Electronics", "price": 1299.99},
    {"product_id": 101, "name": "Headphones", "category": "Accessories", "price": 99.99},
    {"product_id": 202, "name": "Smartwatch", "category": "Electronics", "price": 299.99},
]

# ВАЖНО: Порядок маршрутов имеет значение. Сначала более конкретный /search, потом /{product_id}
@app.get("/products/search")
async def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    """
    Поиск товаров по ключевому слову (в названии) и фильтрация по категории.
    """
    results = []
    for product in sample_products:
        # Поиск по ключевому слову в названии (регистронезависимо)
        if keyword.lower() in product["name"].lower():
            # Фильтр по категории, если она указана
            if category:
                if product["category"].lower() == category.lower():
                    results.append(product)
            else:
                results.append(product)

    # Ограничиваем количество результатов
    limited_results = results[:limit]
    return limited_results


@app.get("/product/{product_id}")
async def get_product(product_id: int):
    """
    Получение товара по его ID.
    """
    product = next((p for p in sample_products if p["product_id"] == product_id), None)
    if product is None:
        # Возвращаем 404, если товар не найден
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# --- Задание 5.4 (Headers) ---
from pydantic import BaseModel, field_validator
import re

class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: Optional[str] = Field(None, alias="Accept-Language")

    @field_validator("accept_language")
    @classmethod
    def validate_accept_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Простейшая проверка формата (наличие ';q=')
        if ';q=' not in v and ',' not in v:
            pass
        return v


@app.get("/headers")
async def get_headers(headers: Annotated[CommonHeaders, Header()]):
    """
    Возвращает User-Agent и Accept-Language из заголовков запроса.
    """
    return headers.model_dump(by_alias=True)


@app.get("/info", response_class=JSONResponse)
async def get_info(
    request: Request,
    headers: Annotated[CommonHeaders, Header()]
):
    """
    Возвращает приветствие, заголовки и добавляет X-Server-Time в заголовки ответа.
    """
    # Получаем текущее серверное время в нужном формате
    server_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    # Создаем ответ
    response_content = {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": headers.model_dump(by_alias=True)
    }

    # Возвращаем ответ с дополнительным заголовком
    return JSONResponse(
        content=response_content,
        headers={"X-Server-Time": server_time}
    )



app.include_router(auth_router, tags=["authentication"])


@app.get("/profile", tags=["profile"])
async def get_profile(current_user: dict = Depends(get_current_user_from_cookie)):
    """
    Защищенный маршрут, возвращающий информацию о пользователе.
    Требует валидной куки session_token.
    """

    return {
        "message": "Добро пожаловать в ваш профиль!",
        "user_id": str(current_user["user_id"]),
        "last_activity": datetime.fromtimestamp(current_user["timestamp"], tz=timezone.utc).isoformat()
    }
