from pydantic import BaseModel, Field, field_validator, EmailStr
import re
from typing import Optional
import uuid



class User(BaseModel):
    name: str
    id: int

class UserAge(BaseModel):
    name: str
    age: int

class Feedback(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    message: str = Field(min_length=10, max_length=500)

    @field_validator("message")
    @classmethod
    def check_bad_words(cls, value):
        bad_words = ["кринж", "рофл", "вайб"]
        for word in bad_words:
            if re.search(word, value, re.IGNORECASE):
                raise ValueError("Использование недопустимых слов")
        return value

# Задание 3.1
class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Имя пользователя, обязательное поле")
    email: EmailStr = Field(..., description="Email, должен быть валидного формата")
    age: Optional[int] = Field(None, gt=0, description="Возраст, должен быть положительным числом")
    is_subscribed: Optional[bool] = Field(False, description="Флаг подписки на рассылку")




# Задание 5.1, 5.2, 5.3 (Модель для логина)
class LoginRequest(BaseModel):
    username: str
    password: str

# Задание 5.3 (Модель для данных пользователя в БД)
class UserInDB(BaseModel):
    id: uuid.UUID
    username: str
    hashed_password: str
