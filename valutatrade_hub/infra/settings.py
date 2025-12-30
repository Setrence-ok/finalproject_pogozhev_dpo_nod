import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import toml


class SingletonMeta(type):
    """
    Мета-класс для реализации паттерна Singleton.
    Гарантирует, что у класса есть только один экземпляр.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class SettingsLoader(metaclass=SingletonMeta):
    """
    Singleton класс для загрузки конфигурации.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Инициализация загрузчика настроек.
        """
        self.config_path = config_path or self._find_config_file()
        self._config = self._load_config()
        self._defaults = self._get_defaults()

    def _find_config_file(self) -> Path:
        """Поиск файла конфигурации в стандартных местах"""
        possible_paths = [
            Path("config.json"),
            Path("config.toml"),
            Path("pyproject.toml"),
            Path("data/config.json"),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # Создаём дефолтный конфиг, если не найден
        default_path = Path("config.json")
        self._create_default_config(default_path)
        return default_path

    def _create_default_config(self, path: Path) -> None:
        """Создание конфигурации по умолчанию"""
        default_config = {
            "data_dir": "data",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_dir": "logs",
            "log_level": "INFO",
            "log_format": "text",
            "log_max_size_mb": 10,
            "log_backup_count": 5,
            "api_timeout": 30,
            "api_max_retries": 3,
            "supported_currencies": ["USD", "EUR", "GBP", "BTC", "ETH"],
        }

        path.parent.mkdir(exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из файла"""
        if not self.config_path.exists():
            return self._get_defaults()

        try:
            if self.config_path.suffix == '.json':
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif self.config_path.suffix == '.toml':
                config_data = toml.load(self.config_path)
                if self.config_path.name == 'pyproject.toml':
                    return config_data.get('tool', {}).get('valutatrade', {})
                return config_data
            else:
                return self._get_defaults()
        except Exception:
            return self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Настройки по умолчанию"""
        return {
            "data_dir": "data",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_dir": "logs",
            "log_level": "INFO",
            "log_format": "text",
            "log_max_size_mb": 10,
            "log_backup_count": 5,
            "api_timeout": 30,
            "api_max_retries": 3,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Получение значения конфигурации.
        """
        # Поиск в загруженной конфигурации
        value = self._config.get(key)
        if value is not None:
            return value

        # Поиск в настройках по умолчанию
        value = self._defaults.get(key)
        if value is not None:
            return value

        # Возврат значения по умолчанию
        return default

    def reload(self) -> None:
        """Перезагрузка конфигурации из файла"""
        self._config = self._load_config()

    def set(self, key: str, value: Any) -> None:
        """Установка значения конфигурации (в памяти)"""
        self._config[key] = value

    def save(self) -> None:
        """Сохранение текущей конфигурации в файл"""
        if self.config_path.suffix == '.json':
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

    # ========== СВОЙСТВА ДЛЯ ЛОГИРОВАНИЯ ==========

    @property
    def data_dir(self) -> Path:
        return Path(self.get("data_dir", "data"))

    @property
    def rates_ttl_seconds(self) -> int:
        return int(self.get("rates_ttl_seconds", 300))

    @property
    def default_base_currency(self) -> str:
        return self.get("default_base_currency", "USD")

    @property
    def log_dir(self) -> Path:
        return Path(self.get("log_dir", "logs"))

    @property
    def log_level(self) -> str:
        return self.get("log_level", "INFO")

    @property
    def log_format(self) -> str:
        return self.get("log_format", "text")

    @property
    def log_max_size_mb(self) -> int:
        return int(self.get("log_max_size_mb", 10))

    @property
    def log_backup_count(self) -> int:
        return int(self.get("log_backup_count", 5))

    @property
    def api_timeout(self) -> int:
        return int(self.get("api_timeout", 30))

    @property
    def api_max_retries(self) -> int:
        return int(self.get("api_max_retries", 3))

    def __getitem__(self, key: str) -> Any:
        """Доступ к настройкам через квадратные скобки"""
        return self.get(key)


# Создаём глобальный экземпляр для удобного доступа
settings = SettingsLoader()