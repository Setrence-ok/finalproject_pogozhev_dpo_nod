import logging
import logging.handlers
import os
from datetime import datetime
from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging():
    """Настройка системы логирования"""
    settings = SettingsLoader()
    log_dir = settings.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Формат логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Основной логгер
    logger = logging.getLogger('valutatrade')
    logger.setLevel(logging.INFO)

    # Очистка предыдущих обработчиков
    if logger.handlers:
        logger.handlers.clear()

    # Файловый обработчик с ротацией
    log_file = os.path.join(log_dir, 'actions.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, datefmt=date_format)
    file_handler.setFormatter(file_formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Получить именованный логгер"""
    return logging.getLogger(f'valutatrade.{name}')