import os
from typing import Any


class SettingsLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Конфигурация из переменных окружения или дефолтные значения
        self._config = {
            "DATA_DIR": "data",
            "RATES_TTL_SECONDS": 300,  # 5 минут
            "DEFAULT_BASE_CURRENCY": "USD",
            "LOG_DIR": "logs",
            "LOG_FORMAT": "string",  # или "json"
            "EXCHANGERATE_API_KEY": os.getenv("EXCHANGERATE_API_KEY", "c7ef33caebf0f8f2f5ee6bd3"),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def reload(self):
        self._initialize()