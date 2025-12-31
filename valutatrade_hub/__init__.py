"""ValutaTrade Hub - Платформа для отслеживания и симуляции торговли валютами"""

__version__ = "1.0.0"

# Инициализируем систему логирования при импорте
from .logging_config import setup_logging

# Настраиваем логирование при запуске
setup_logging()

__all__ = ['__version__']