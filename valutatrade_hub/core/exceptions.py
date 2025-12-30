class InsufficientFundsError(Exception):
    """Исключение: недостаточно средств"""

    def __init__(self, currency_code: str, available: float, required: float):
        self.currency_code = currency_code
        self.available = available
        self.required = required
        super().__init__(
            f"Недостаточно средств: доступно {available} {currency_code}, "
            f"требуется {required} {currency_code}"
        )


class CurrencyNotFoundError(Exception):
    """Исключение: неизвестная валюта"""

    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"Неизвестная валюта '{currency_code}'")


class ApiRequestError(Exception):
    """Исключение: ошибка обращения к внешнему API"""

    def __init__(self, reason: str = "Неизвестная ошибка"):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")


class UserNotFoundError(Exception):
    """Исключение: пользователь не найден"""

    def __init__(self, username: str):
        self.username = username
        super().__init__(f"Пользователь '{username}' не найден")


class InvalidPasswordError(Exception):
    """Исключение: неверный пароль"""

    def __init__(self):
        super().__init__("Неверный пароль")


class WalletNotFoundError(Exception):
    """Исключение: кошелёк не найден"""

    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        super().__init__(f"У вас нет кошелька '{currency_code}'")


class InvalidAmountError(Exception):
    """Исключение: неверная сумма"""

    def __init__(self, amount):
        super().__init__(f"Сумма должна быть положительным числом, получено: {amount}")


class AuthenticationError(Exception):
    """Исключение: ошибка аутентификации"""

    def __init__(self):
        super().__init__("Сначала выполните login")