import json
import os
from typing import Any, Dict, List
from pathlib import Path


class JSONFileManager:
    """Менеджер для работы с JSON файлами"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _get_file_path(self, filename: str) -> Path:
        """Получение полного пути к файлу"""
        return self.data_dir / filename

    def load_json(self, filename: str, default: Any = None) -> Any:
        """Загрузка данных из JSON файла"""
        file_path = self._get_file_path(filename)

        if not file_path.exists():
            if default is not None:
                self.save_json(filename, default)
            return default or {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return default or {}

    def save_json(self, filename: str, data: Any) -> None:
        """Сохранение данных в JSON файл"""
        file_path = self._get_file_path(filename)

        # Создаем директорию, если её нет
        file_path.parent.mkdir(exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def append_to_json(self, filename: str, item: Any, key_field: str = "id") -> None:
        """Добавление элемента в JSON файл (для списков)"""
        data = self.load_json(filename, [])

        if isinstance(data, list):
            # Находим максимальный ID
            max_id = max([item.get(key_field, 0) for item in data], default=0)
            item[key_field] = max_id + 1
            data.append(item)
            self.save_json(filename, data)
        else:
            raise ValueError("Данные не являются списком")


def validate_currency_code(currency_code: str) -> str:
    """Валидация кода валюты"""
    if not currency_code or not isinstance(currency_code, str):
        raise ValueError("Код валюты должен быть непустой строкой")

    currency_code = currency_code.upper().strip()
    if len(currency_code) not in range(2, 6):
        raise ValueError("Код валюты должен содержать 2-5 символов")

    return currency_code


def validate_amount(amount: float) -> float:
    """Валидация суммы"""
    if not isinstance(amount, (int, float)):
        raise TypeError("Сумма должна быть числом")

    amount = float(amount)
    if amount <= 0:
        raise ValueError("Сумма должна быть положительным числом")

    return amount


def format_currency(value: float, currency: str = "USD") -> str:
    """Форматирование денежных значений"""
    if currency in ["USD", "EUR", "GBP"]:
        return f"{value:,.2f} {currency}"
    elif currency in ["BTC", "ETH"]:
        return f"{value:.8f} {currency}"
    else:
        return f"{value:.2f} {currency}"