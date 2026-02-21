from pydantic import BaseModel, Field, field_validator
import re

# Задание 1.4
class User(BaseModel):
    name: str
    id: int


# Задание 1.5
class UserAge(BaseModel):
    name: str
    age: int


# Задание 2.1 и 2.2
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
