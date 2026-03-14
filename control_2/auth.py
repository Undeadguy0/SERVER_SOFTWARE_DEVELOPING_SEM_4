from fastapi import APIRouter, HTTPException, Response, Request, Depends, status
from models import LoginRequest
import uuid
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import time
from datetime import datetime, timezone
import os

SECRET_KEY = os.getenv("SECRET_KEY", "my-very-secret-key-change-in-production")
serializer = URLSafeTimedSerializer(secret_key=SECRET_KEY, salt="session-cookie")

# Время жизни сессии в секундах (5 минут)
SESSION_DURATION = 300
# Порог для продления сессии (3 минуты)
RENEWAL_THRESHOLD = 180
router = APIRouter()

# типо БД
fake_users_db = {
    "alice": {
        "id": uuid.uuid4(),
        "username": "alice",
        "password": "password123",
    },
    "bob": {
        "id": uuid.uuid4(),
        "username": "bob",
        "password": "secret",
    }
}


def verify_user(username: str, password: str):
    """Проверяет учетные данные пользователя."""
    user = fake_users_db.get(username)
    if user and user["password"] == password:
        return user
    return None

def create_session_token(user_id: uuid.UUID, timestamp: int = None) -> str:
    """
    Создает подписанную строку для куки в формате <user_id>.<timestamp>.
    Если timestamp не передан, используется текущее время.
    """
    if timestamp is None:
        timestamp = int(time.time())
    data = {
        "user_id": str(user_id),
        "timestamp": timestamp
    }
    signed_data = serializer.dumps(data)
    return signed_data

def parse_and_verify_session_token(token: str, max_age: int = SESSION_DURATION):
    """
    Разбирает и проверяет подпись и время жизни токена.
    Возвращает исходные данные (user_id, timestamp) или вызывает HTTPException.
    max_age - максимально допустимый возраст токена в секундах.
    """
    try:
        # loads проверяет подпись и срок действия (по max_age)
        data = serializer.loads(token, max_age=max_age)
        # Преобразуем user_id обратно в UUID
        user_id = uuid.UUID(data["user_id"])
        timestamp = data["timestamp"]
        return {"user_id": user_id, "timestamp": timestamp}
    except SignatureExpired:
        # Подпись верна, но срок истек
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    except BadSignature:
        # Подпись недействительна (данные были изменены)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    except Exception:
        # Любая другая ошибка (например, неправильный формат)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session format"
        )

def should_renew_session(token_timestamp: int) -> bool:
    """
    Определяет, нужно ли продлить сессию.
    Возвращает True, если с timestamp прошло от 3 до 5 минут.
    """
    now = int(time.time())
    elapsed = now - token_timestamp
    # Продлеваем, если прошло >= 3 минут (RENEWAL_THRESHOLD) и < 5 минут (SESSION_DURATION)
    return RENEWAL_THRESHOLD <= elapsed < SESSION_DURATION

async def get_current_user_from_cookie(request: Request) -> dict:
    """
    Зависимость FastAPI, которая извлекает и проверяет куку session_token.
    Используется в защищенных маршрутах (например, /profile).
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    # Проверяем токен. max_age устанавливаем чуть больше, чем нужно,
    user_data = parse_and_verify_session_token(token, max_age=SESSION_DURATION)
    return user_data


# Задания 5.1 и 5.2 (базовый логин с подписью)
@router.post("/login")
async def login(login_data: LoginRequest, response: Response):
    """
    Аутентифицирует пользователя и устанавливает подписанную куку session_token.
    Формат куки: <user_id>.<timestamp>.<signature>
    """
    user = verify_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Создаем подписанный токен с текущим временем
    session_token = create_session_token(user["id"])

    # Устанавливаем куку
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=SESSION_DURATION,
        secure=False,
        samesite="lax"
    )
    return {"message": "Login successful"}


# Задание 5.3 (расширенный логин с динамическим продлением)
# Защищенный маршрут, который также обновляет куку (для задания 5.3)
@router.get("/secure-profile")
async def secure_profile(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user_from_cookie)
):
    """
    Защищенный маршрут, который проверяет сессию и продлевает её при необходимости.
    """
    # Теперь проверяем, нужно ли продлевать сессию.
    token_timestamp = current_user["timestamp"]
    now = int(time.time())
    elapsed = now - token_timestamp

    # Проверяем, не истекла ли сессия
    if elapsed >= SESSION_DURATION:
        # Теоретически сюда мы не должны попасть, т.к. зависимость выбросит 401.
        raise HTTPException(status_code=401, detail="Session expired")

    # Обновляем куку, если это необходимо
    if should_renew_session(token_timestamp):
        new_timestamp = now
        new_token = create_session_token(current_user["user_id"], new_timestamp)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            max_age=SESSION_DURATION,
            secure=False,
            samesite="lax"
        )
        print(f"Session renewed for user {current_user['user_id']} at {new_timestamp}") # Для отладки

    # Формируем ответ с данными профиля
    profile_data = {
        "user_id": str(current_user["user_id"]),
        "session_created_at": datetime.fromtimestamp(token_timestamp, tz=timezone.utc).isoformat(),
        "current_time": datetime.fromtimestamp(now, tz=timezone.utc).isoformat(),
        "session_duration_elapsed": elapsed,
        "session_renewed": should_renew_session(token_timestamp) # Показываем, было ли обновление
    }
    return profile_data

# Маршрут для логаута (очистка куки)
@router.post("/logout")
async def logout(response: Response):
    """
    Удаляет куку session_token.
    """
    response.delete_cookie("session_token")
    return {"message": "Logged out successfully"}
