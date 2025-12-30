import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from .settings import settings, SettingsLoader
from ..core.exceptions import ApiRequestError


class DatabaseManager(metaclass=type(SettingsLoader)):
    """
    Singleton класс для управления JSON (базой данных).
    Обеспечивает потокобезопасный доступ к данным.
    """

    def __init__(self):
        self.data_dir = settings.data_dir
        self._lock = threading.RLock()  # Reentrant lock для вложенных вызовов

    def _get_file_path(self, filename: str) -> Path:
        """Получение полного пути к файлу"""
        return self.data_dir / filename

    def load_data(self, filename: str, default: Any = None) -> Any:
        """
        Загрузка данных из файла с блокировкой.

        Args:
            filename: Имя файла
            default: Значение по умолчанию, если файл не существует

        Returns:
            Загруженные данные
        """
        file_path = self._get_file_path(filename)

        with self._lock:
            if not file_path.exists():
                if default is not None:
                    self.save_data(filename, default)
                return default or {} if filename.endswith('.json') else []

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return default or {} if filename.endswith('.json') else []

    def save_data(self, filename: str, data: Any) -> None:
        """
        Сохранение данных в файл с блокировкой.

        Args:
            filename: Имя файла
            data: Данные для сохранения
        """
        file_path = self._get_file_path(filename)

        with self._lock:
            # Создаём директорию, если её нет
            file_path.parent.mkdir(exist_ok=True)

            # Создаем временную копию для атомарности записи
            temp_path = file_path.with_suffix('.tmp')

            try:
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)

                # Атомарная замена файла
                temp_path.replace(file_path)
            except Exception as e:
                # Удаляем временный файл при ошибке
                if temp_path.exists():
                    temp_path.unlink()
                raise

    def update_data(self, filename: str, key: str, value: Any) -> None:
        """
        Обновление значения по ключу в JSON файле.

        Args:
            filename: Имя файла
            key: Ключ для обновления
            value: Новое значение
        """
        with self._lock:
            data = self.load_data(filename, {})
            if isinstance(data, dict):
                data[key] = value
                self.save_data(filename, data)
            else:
                raise ValueError(f"Данные в файле {filename} не являются словарём")

    def append_to_list(self, filename: str, item: Any) -> None:
        """
        Добавление элемента в список в JSON файле.

        Args:
            filename: Имя файла
            item: Элемент для добавления
        """
        with self._lock:
            data = self.load_data(filename, [])
            if isinstance(data, list):
                data.append(item)
                self.save_data(filename, data)
            else:
                raise ValueError(f"Данные в файле {filename} не являются списком")

    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        return self.load_data("users.json", [])

    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Поиск пользователя по имени"""
        users = self.get_all_users()
        for user in users:
            if user.get("username") == username:
                return user
        return None

    def save_user(self, user_data: Dict) -> None:
        """Сохранение пользователя"""
        users = self.get_all_users()
        users.append(user_data)
        self.save_data("users.json", users)

    def get_portfolio(self, user_id: int) -> Optional[Dict]:
        """Получение портфеля пользователя"""
        portfolios = self.load_data("portfolios.json", {})
        return portfolios.get(str(user_id))

    def save_portfolio(self, user_id: int, portfolio_data: Dict) -> None:
        """Сохранение портфеля пользователя"""
        portfolios = self.load_data("portfolios.json", {})
        portfolios[str(user_id)] = portfolio_data
        self.save_data("portfolios.json", portfolios)

    def get_exchange_rates(self) -> Dict:
        """Получение текущих курсов валют"""
        rates = self.load_data("rates.json", {})

        # Проверка свежести данных
        if not rates or not rates.get("last_refresh"):
            # Если данных нет или они устарели, обновляем
            rates = self._refresh_exchange_rates()

        return rates

    def _refresh_exchange_rates(self) -> Dict:
        """Обновление курсов валют (заглушка)"""
        # В реальном проекте здесь был бы запрос к API
        # Для демонстрации используем фиксированные значения

        new_rates = {
            "last_refresh": datetime.now().isoformat(),
            "source": "MockAPI",
            "rates": {
                "EUR_USD": {
                    "rate": 1.0786,
                    "updated_at": datetime.now().isoformat()
                },
                "BTC_USD": {
                    "rate": 59337.21,
                    "updated_at": datetime.now().isoformat()
                },
                "RUB_USD": {
                    "rate": 0.01016,
                    "updated_at": datetime.now().isoformat()
                },
                "ETH_USD": {
                    "rate": 3720.00,
                    "updated_at": datetime.now().isoformat()
                },
                "USD_EUR": {
                    "rate": 0.9271,
                    "updated_at": datetime.now().isoformat()
                },
                "USD_BTC": {
                    "rate": 0.00001685,
                    "updated_at": datetime.now().isoformat()
                },
            }
        }

        self.save_data("rates.json", new_rates)
        return new_rates

    def is_rate_fresh(self) -> bool:
        """Проверка свежести курсов валют"""
        rates = self.load_data("rates.json", {})

        if not rates or "last_refresh" not in rates:
            return False

        try:
            last_refresh = datetime.fromisoformat(rates["last_refresh"])
            now = datetime.now()
            ttl_seconds = settings.rates_ttl_seconds

            return (now - last_refresh).total_seconds() <= ttl_seconds
        except (ValueError, TypeError):
            return False


# Глобальный экземпляр для удобного доступа
db = DatabaseManager()