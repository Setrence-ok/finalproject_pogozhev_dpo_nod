import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class User:
    def __init__(
            self,
            user_id: int,
            username: str,
            password: str = "",  # Может быть пустым при загрузке из БД
            salt: Optional[str] = None,
            registration_date: Optional[str] = None,
            hashed_password: Optional[str] = None  # Новый параметр для загрузки из БД
    ):
        self.__user_id = user_id
        self.__username = username

        # ИСПРАВЛЕНИЕ: Правильная обработка при загрузке из БД
        if hashed_password and salt:
            # При загрузке из БД используем готовые значения
            self.__hashed_password = hashed_password
            self.__salt = salt
            logger.debug(f"User loaded from DB: {username}, hash exists")
        else:
            # При создании нового пользователя генерируем соль и хеш
            self.__salt = salt or self._generate_salt(user_id)
            if password:
                self.__hashed_password = self._hash_password(password, self.__salt)
                logger.debug(f"New user created: {username}, hash generated")
            else:
                raise ValueError("Password required for new user")

        # Дата регистрации
        if registration_date:
            self.__registration_date = registration_date
        else:
            self.__registration_date = datetime.now().isoformat()

    def _generate_salt(self, user_id: int) -> str:
        """Генерация уникальной соли"""
        import time
        # Используем комбинацию user_id и времени для уникальности
        base = f"{user_id}_{time.time_ns()}_{hashlib.sha256(str(user_id).encode()).hexdigest()[:8]}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]

    def _hash_password(self, password: str, salt: str) -> str:
        """Хеширование пароля с солью (UTF-8 кодировка)"""
        data = (password + salt).encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    # ========== ГЕТТЕРЫ ==========
    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def hashed_password(self) -> str:
        return self.__hashed_password

    @property
    def salt(self) -> str:
        return self.__salt

    @property
    def registration_date(self) -> str:
        return self.__registration_date

    # ========== СЕТТЕРЫ ==========
    @username.setter
    def username(self, value: str):
        if not value or len(value.strip()) == 0:
            raise ValueError("Имя пользователя не может быть пустым")
        self.__username = value

    # ========== МЕТОДЫ ==========
    def verify_password(self, password: str) -> bool:
        """Проверка пароля с подробным логированием для отладки"""
        if not password:
            logger.warning(f"Empty password provided for user {self.__username}")
            return False

        computed_hash = self._hash_password(password, self.__salt)
        is_valid = self.__hashed_password == computed_hash

        logger.debug(f"Password verification for {self.__username}:")
        logger.debug(f"  Provided password: {'*' * len(password)}")
        logger.debug(f"  Salt used: {self.__salt}")
        logger.debug(f"  Stored hash: {self.__hashed_password[:20]}...")
        logger.debug(f"  Computed hash: {computed_hash[:20]}...")
        logger.debug(f"  Result: {'VALID' if is_valid else 'INVALID'}")

        return is_valid

    def change_password(self, new_password: str):
        """Изменение пароля"""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self.__hashed_password = self._hash_password(new_password, self.__salt)

    def get_user_info(self) -> Dict[str, Any]:
        """Возвращает информацию о пользователе (без пароля)"""
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "registration_date": self.__registration_date
        }

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь для JSON"""
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "hashed_password": self.__hashed_password,
            "salt": self.__salt,
            "registration_date": self.__registration_date
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Десериализация из словаря"""
        logger.debug(f"Loading user from dict: username={data.get('username')}")

        # ВАЖНО: При загрузке из БД передаем готовый хеш и соль
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            password="",  # Пустой пароль, т.к. хеш уже есть
            salt=data["salt"],
            registration_date=data["registration_date"],
            hashed_password=data["hashed_password"]  # Готовый хеш из БД
        )

    def __str__(self) -> str:
        return f"User(id={self.__user_id}, username='{self.__username}')"

    def __repr__(self) -> str:
        return f"User(user_id={self.__user_id}, username='{self.__username}')"


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.__currency_code = currency_code.upper()
        self.__balance = float(balance)

    # ========== СВОЙСТВА ==========
    @property
    def currency_code(self) -> str:
        return self.__currency_code

    @property
    def balance(self) -> float:
        return self.__balance

    @balance.setter
    def balance(self, value: float):
        """Запрещает отрицательный баланс"""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self.__balance = float(value)

    # ========== МЕТОДЫ ==========
    def deposit(self, amount: float):
        """Пополнение кошелька"""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance = self.__balance + amount

    def withdraw(self, amount: float):
        """Снятие средств"""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.__balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.__balance}")
        self.balance = self.__balance - amount

    def get_balance_info(self) -> dict:
        """Информация о балансе"""
        return {
            "currency_code": self.__currency_code,
            "balance": self.__balance
        }

    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON"""
        return {
            "currency_code": self.__currency_code,
            "balance": self.__balance
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Wallet':
        """Десериализация из словаря"""
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    def __init__(self, user_id: int, wallets: dict[str, Wallet] = None):
        self.__user_id = user_id
        self.__wallets = wallets or {}

    # ========== СВОЙСТВА ==========
    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def wallets(self) -> dict:
        """Возвращает копию словаря кошельков"""
        return self.__wallets.copy()

    # ========== МЕТОДЫ ==========
    def add_currency(self, currency_code: str) -> Wallet:
        """Добавляет новую валюту в портфель"""
        currency_code = currency_code.upper()
        if currency_code in self.__wallets:
            raise ValueError(f"Валюта {currency_code} уже есть в портфеле")

        wallet = Wallet(currency_code)
        self.__wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелёк по коду валюты"""
        currency_code = currency_code.upper()
        return self.__wallets.get(currency_code)

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Рассчитывает общую стоимость портфеля в базовой валюте"""
        # Фиксированные курсы для демонстрации
        exchange_rates = {
            "USD": 1.0,
            "EUR": 1.08,
            "BTC": 59337.21,
            "ETH": 3720.00,
            "RUB": 0.01016
        }

        total = 0.0
        for wallet in self.__wallets.values():
            # Конвертация в базовую валюту
            if wallet.currency_code == base_currency:
                total += wallet.balance
            else:
                # Конвертация через USD как промежуточную валюту
                rate_to_usd = exchange_rates.get(wallet.currency_code, 0)
                rate_base_to_usd = exchange_rates.get(base_currency, 1)
                if rate_to_usd > 0:
                    value_in_usd = wallet.balance * rate_to_usd
                    value_in_base = value_in_usd / rate_base_to_usd
                    total += value_in_base
        return total

    def to_dict(self) -> dict:
        """Сериализация в словарь для JSON"""
        return {
            "user_id": self.__user_id,
            "wallets": {
                code: wallet.to_dict()
                for code, wallet in self.__wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Portfolio':
        """Десериализация из словаря"""
        wallets = {
            code: Wallet.from_dict(wallet_data)
            for code, wallet_data in data["wallets"].items()
        }
        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )