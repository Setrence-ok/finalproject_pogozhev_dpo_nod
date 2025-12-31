import functools
import logging
from datetime import datetime
from typing import Callable, Any

from .logging_config import get_logger


def log_action(action_name: str = None, verbose: bool = False):
    """
    Декоратор для логирования действий пользователя.

    Args:
        action_name: Название действия (BUY/SELL/REGISTER/LOGIN)
        verbose: Подробное логирование с состоянием до/после
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('actions')

            # Извлекаем информацию о пользователе из аргументов
            user_info = {}
            try:
                # Пытаемся найти user_id в аргументах
                for arg in args:
                    if hasattr(arg, 'user_id'):
                        user_info['user_id'] = arg.user_id
                    if hasattr(arg, 'username'):
                        user_info['username'] = arg.username

                # Или в kwargs
                if 'user_id' in kwargs:
                    user_info['user_id'] = kwargs['user_id']
                if 'username' in kwargs:
                    user_info['username'] = kwargs['username']
            except:
                pass

            action = action_name or func.__name__.upper()

            # Подготовка данных для лога
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'function': func.__name__,
                'username': user_info.get('username', 'unknown'),
                'user_id': user_info.get('user_id', 'unknown'),
            }

            # Добавляем параметры если verbose
            if verbose:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)

                # Логируем успех
                log_data['result'] = 'OK'
                if verbose and hasattr(result, 'to_dict'):
                    log_data['result_data'] = str(result.to_dict())

                logger.info(f"{action} - Успех: {log_data}")

                return result

            except Exception as e:
                # Логируем ошибку
                log_data['result'] = 'ERROR'
                log_data['error_type'] = type(e).__name__
                log_data['error_message'] = str(e)

                logger.error(f"{action} - Ошибка: {log_data}")

                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator