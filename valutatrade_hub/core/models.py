import hashlib
from datetime import datetime
from typing import Dict, Optional


class User:
    def __init__(self, user_id: int, username: str, hashed_password: str,
                 salt: str, registration_date: datetime):
        self.__user_id = user_id
        self.__username = username
        self.__hashed_password = hashed_password
        self.__salt = salt
        self.__registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self.__username = value

    @property
    def hashed_password(self) -> str:
        return self.__hashed_password

    @property
    def salt(self) -> str:
        return self.__salt

    @property
    def registration_date(self) -> datetime:
        return self.__registration_date

    def get_user_info(self) -> str:
        return (f"ID: {self.__user_id}, "
                f"Имя: {self.__username}, "
                f"Дата регистрации: {self.__registration_date}")

    def change_password(self, new_password: str):
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        new_salt = self.__generate_salt()
        new_hashed = self.__hash_password(new_password, new_salt)
        self.__hashed_password = new_hashed
        self.__salt = new_salt

    def verify_password(self, password: str) -> bool:
        hashed_input = self.__hash_password(password, self.__salt)
        return hashed_input == self.__hashed_password

    def to_dict(self) -> Dict:
        return {
            "user_id": self.__user_id,
            "username": self.__username,
            "hashed_password": self.__hashed_password,
            "salt": self.__salt,
            "registration_date": self.__registration_date.isoformat()
        }

    @staticmethod
    def __generate_salt() -> str:
        import secrets
        return secrets.token_hex(8)

    @staticmethod
    def __hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            hashed_password=data["hashed_password"],
            salt=data["salt"],
            registration_date=datetime.fromisoformat(data["registration_date"])
        )

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя не может быть пустым")
        self.__username = value.strip()  # Добавим strip()


class Wallet:
    def __init__(self, currency_code: str, balance: float = 0.0):
        self.__currency_code = currency_code
        self.__balance = balance

    @property
    def currency_code(self) -> str:
        return self.__currency_code

    @property
    def balance(self) -> float:
        return self.__balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self.__balance = float(value)

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance = self.__balance + amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.__balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.__balance}")
        self.balance = self.__balance - amount

    def get_balance_info(self) -> str:
        return f"{self.__currency_code}: {self.__balance:.4f}"

    def to_dict(self) -> Dict:
        return {
            "currency_code": self.__currency_code,
            "balance": self.__balance
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Wallet':
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )


class Portfolio:
    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        self.__user_id = user_id
        self.__wallets = wallets or {}

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self.__wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        if currency_code in self.__wallets:
            raise ValueError(f"Валюта {currency_code} уже есть в портфеле")

        wallet = Wallet(currency_code)
        self.__wallets[currency_code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        return self.__wallets.get(currency_code)

    def get_total_value(self, base_currency: str = 'USD') -> float:
        # Временная заглушка - в реальности будет использоваться rates.json
        exchange_rates = {
            "EUR_USD": 1.0786,
            "BTC_USD": 59337.21,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "USD_USD": 1.0
        }

        total = 0.0
        for wallet in self.__wallets.values():
            rate_key = f"{wallet.currency_code}_{base_currency}"
            if rate_key in exchange_rates:
                rate = exchange_rates[rate_key]
                total += wallet.balance * rate
            elif wallet.currency_code == base_currency:
                total += wallet.balance

        return total

    def to_dict(self) -> Dict:
        return {
            "user_id": self.__user_id,
            "wallets": {
                code: wallet.to_dict()
                for code, wallet in self.__wallets.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        wallets = {}
        for code, wallet_data in data.get("wallets", {}).items():
            wallets[code] = Wallet.from_dict(wallet_data)

        return cls(
            user_id=data["user_id"],
            wallets=wallets
        )