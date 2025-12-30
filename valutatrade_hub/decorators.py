import functools
import time
from typing import Callable, Any, Optional, Dict
from datetime import datetime

from .logging_config import get_logger
from .core.exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError

logger = get_logger("actions")


def log_action(action: str, verbose: bool = False):
    """
    Декоратор для логирования действий пользователя.

    Args:
        action: Название действия (BUY, SELL, REGISTER, LOGIN и т.д.)
        verbose: Подробное логирование (добавляет контекст)

    Returns:
        Декорированная функция
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Подготовка контекста для логирования
            log_context = {
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "function": func.__name__,
                "module": func.__module__,
            }

            # Извлекаем полезные аргументы из функции
            try:
                # Для методов usecases, первый аргумент - self, второй - user_id
                if len(args) >= 2 and hasattr(args[0], '__class__'):
                    log_context["user_id"] = args[1] if len(args) > 1 else "unknown"

                # Ищем username в kwargs или args
                if 'username' in kwargs:
                    log_context["username"] = kwargs['username']
                elif len(args) >= 2 and isinstance(args[1], str):
                    # Предполагаем, что второй аргумент - username для register/login
                    log_context["username"] = args[1]

                # Ищем currency и amount
                if 'currency_code' in kwargs:
                    log_context["currency"] = kwargs['currency_code']
                elif 'currency' in kwargs:
                    log_context["currency"] = kwargs['currency']

                if 'amount' in kwargs:
                    log_context["amount"] = kwargs['amount']
            except (IndexError, AttributeError):
                pass

            start_time = time.time()
            result = "OK"
            error_info = {}

            try:
                # Выполнение функции
                func_result = func(*args, **kwargs)

                # Добавляем результат в контекст, если нужно
                if verbose and func_result:
                    if isinstance(func_result, dict):
                        log_context.update({f"result_{k}": v for k, v in func_result.items()})
                    else:
                        log_context["result"] = str(func_result)

                return func_result

            except InsufficientFundsError as e:
                result = "ERROR"
                error_info = {
                    "error_type": "InsufficientFundsError",
                    "error_message": str(e),
                    "currency": getattr(e, 'currency_code', 'unknown'),
                    "available": getattr(e, 'available', 0),
                    "required": getattr(e, 'required', 0),
                }
                raise

            except CurrencyNotFoundError as e:
                result = "ERROR"
                error_info = {
                    "error_type": "CurrencyNotFoundError",
                    "error_message": str(e),
                    "currency": getattr(e, 'currency_code', 'unknown'),
                }
                raise

            except ApiRequestError as e:
                result = "ERROR"
                error_info = {
                    "error_type": "ApiRequestError",
                    "error_message": str(e),
                    "reason": getattr(e, 'reason', 'unknown'),
                }
                raise

            except Exception as e:
                result = "ERROR"
                error_info = {
                    "error_type": e.__class__.__name__,
                    "error_message": str(e),
                }
                raise

            finally:
                # Логирование результата
                execution_time = time.time() - start_time
                log_context.update({
                    "result": result,
                    "execution_time_ms": round(execution_time * 1000, 2),
                    **error_info,
                })

                if result == "OK":
                    logger.info(f"{action} completed successfully", extra=log_context)
                else:
                    logger.error(f"{action} failed", extra=log_context)

        return wrapper

    return decorator


def measure_time(func: Callable) -> Callable:
    """Декоратор для измерения времени выполнения функции"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger.debug(
            f"Function {func.__name__} executed in {end_time - start_time:.4f} seconds",
            extra={
                "function": func.__name__,
                "execution_time": end_time - start_time,
            }
        )

        return result

    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Декоратор для повторной попытки выполнения при ошибках.

    Args:
        max_retries: Максимальное количество попыток
        delay: Задержка между попытками в секундах

    Returns:
        Декорированная функция
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (ApiRequestError, ConnectionError, TimeoutError) as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay} seconds...",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "error": str(e),
                            }
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "error": str(e),
                            }
                        )

            # Если все попытки провалились, пробрасываем последнее исключение
            raise last_exception if last_exception else Exception("Unknown error")

        return wrapper

    return decorator