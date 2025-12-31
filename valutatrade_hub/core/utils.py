import json
import os
from typing import Optional
from datetime import datetime
from .models import User
from ..infra.database import DatabaseManager


class SessionManager:
    _SESSION_FILE = "data/session.json"

    @classmethod
    def _ensure_session_file(cls):
        """Создать файл сессии если его нет"""
        if not os.path.exists(cls._SESSION_FILE):
            os.makedirs(os.path.dirname(cls._SESSION_FILE), exist_ok=True)
            with open(cls._SESSION_FILE, 'w') as f:
                json.dump({}, f)

    @classmethod
    def login(cls, user: User):
        """Сохранить сессию в файл"""
        cls._ensure_session_file()

        session_data = {
            'user_id': user.user_id,
            'username': user.username,
            'login_time': datetime.now().isoformat(),
            'hashed_password': user.hashed_password  # для проверки при восстановлении
        }

        with open(cls._SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

    @classmethod
    def logout(cls):
        """Завершить сессию"""
        cls._ensure_session_file()
        with open(cls._SESSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

    @classmethod
    def get_current_user(cls) -> Optional[User]:
        """Восстановить пользователя из файла сессии"""
        cls._ensure_session_file()

        try:
            with open(cls._SESSION_FILE, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            if not session_data or 'user_id' not in session_data:
                return None

            # Загружаем пользователя из базы данных
            db = DatabaseManager()
            users = db.load_users()

            user_data = next(
                (u for u in users if u['user_id'] == session_data['user_id']),
                None
            )

            if not user_data:
                cls.logout()  # очищаем невалидную сессию
                return None

            # Проверяем, не изменился ли пароль
            if user_data['hashed_password'] != session_data.get('hashed_password'):
                cls.logout()  # пароль изменился - завершаем сессию
                return None

            return User.from_dict(user_data)

        except (json.JSONDecodeError, FileNotFoundError, KeyError):
            return None

    @classmethod
    def is_logged_in(cls) -> bool:
        """Проверить, есть ли активная сессия"""
        return cls.get_current_user() is not None

    @classmethod
    def get_current_user_id(cls) -> Optional[int]:
        """Получить ID текущего пользователя"""
        user = cls.get_current_user()
        return user.user_id if user else None