from fastapi import FastAPI
from fastapi.responses import FileResponse
from models import User, UserAge, Feedback

app = FastAPI()


# Задание 1.1


@app.get("/")
def root():
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}



# Задание 1.2


@app.get("/html")
def get_html():
    return FileResponse("index.html")



# Задание 1.3

@app.post("/calculate")
def calculate(num1: int, num2: int):
    result = num1 + num2
    return {"result": result}



# Задание 1.4


user = User(
    name="Ваше Имя Фамилия",
    id=1
)

@app.get("/users")
def get_user():
    return user



# Задание 1.5


@app.post("/user")
def check_user(user: UserAge):
    is_adult = user.age >= 18

    return {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }



# Задание 2.1 и 2.2


feedbacks = []

@app.post("/feedback")
def create_feedback(feedback: Feedback):

    feedbacks.append(feedback)

    return {
        "message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."
    }



@app.get("/feedback")
def get_feedbacks():
    return feedbacks
