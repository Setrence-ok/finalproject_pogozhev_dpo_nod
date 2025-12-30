import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

from .infra.settings import settings


def setup_logging():
    """
    Настройка системы логирования.
    Создаёт директорию для логов и настраивает handlers.
    """
    log_dir = settings.log_dir
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "actions.log"

    # Форматер
    if settings.log_format == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # File handler с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=settings.log_max_size_mb * 1024 * 1024,  # MB to bytes
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, settings.log_level))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Отключаем логирование от внешних библиотек
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    return root_logger


class JsonFormatter(logging.Formatter):
    """Форматер для JSON логов"""

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Добавляем дополнительные поля из record.args, если они есть
        if hasattr(record, 'extra'):
            log_object.update(record.extra)

        return json.dumps(log_object, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера с заданным именем.

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


# Инициализация логирования при импорте модуля
logger = get_logger("valutatrade_hub")