import hashlib
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .models import User, Portfolio, Wallet
from .utils import JSONFileManager, validate_currency_code, validate_amount


class UserManager:
    """Менеджер пользователей"""

    def __init__(self):
        self.file_manager = JSONFileManager()
        self.current_user: Optional[User] = None

    def register(self, username: str, password: str) -> User:
        """Регистрация нового пользователя"""
        # Загрузка существующих пользователей
        users_data = self.file_manager.load_json("users.json", [])

        # Проверка уникальности username
        for user_data in users_data:
            if user_data["username"] == username:
                raise ValueError(f"Имя пользователя '{username}' уже занято")

        # Проверка пароля
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        # Генерация user_id
        user_id = max([u.get("user_id", 0) for u in users_data], default=0) + 1

        # Создание пользователя
        user = User(user_id=user_id, username=username, password=password)

        # Сохранение пользователя
        users_data.append(user.to_dict())
        self.file_manager.save_json("users.json", users_data)

        # Создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        self._save_portfolio(portfolio)

        return user

    def login(self, username: str, password: str) -> User:
        """Вход пользователя"""
        users_data = self.file_manager.load_json("users.json", [])

        # Поиск пользователя
        user_data = None
        for u in users_data:
            if u["username"] == username:
                user_data = u
                break

        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        # Создание объекта User
        user = User.from_dict(user_data)

        # Проверка пароля
        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        self.current_user = user
        return user

    def logout(self) -> None:
        """Выход пользователя"""
        self.current_user = None

    def _save_portfolio(self, portfolio: Portfolio) -> None:
        """Сохранение портфеля"""
        portfolios_data = self.file_manager.load_json("portfolios.json", {})
        portfolios_data[str(portfolio.user_id)] = portfolio.to_dict()
        self.file_manager.save_json("portfolios.json", portfolios_data)

    def get_current_portfolio(self) -> Optional[Portfolio]:
        """Получение портфеля текущего пользователя"""
        if not self.current_user:
            return None

        portfolios_data = self.file_manager.load_json("portfolios.json", {})
        user_portfolio = portfolios_data.get(str(self.current_user.user_id))

        if user_portfolio:
            return Portfolio.from_dict(user_portfolio)
        else:
            # Создание пустого портфеля, если не существует
            portfolio = Portfolio(user_id=self.current_user.user_id)
            self._save_portfolio(portfolio)
            return portfolio


class PortfolioManager:
    """Менеджер портфелей и операций"""

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self.file_manager = JSONFileManager()

        # Фиксированные курсы для демонстрации
        self.exchange_rates = self._load_exchange_rates()

    def _load_exchange_rates(self) -> Dict[str, Dict]:
        """Загрузка курсов валют"""
        return self.file_manager.load_json("rates.json", {
            "last_refresh": datetime.now().isoformat(),
            "rates": {
                "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat()},
                "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat()},
                "RUB_USD": {"rate": 0.01016, "updated_at": datetime.now().isoformat()},
                "ETH_USD": {"rate": 3720.00, "updated_at": datetime.now().isoformat()},
            }
        })

    def show_portfolio(self, base_currency: str = "USD") -> Tuple[Dict, float]:
        """Показать портфель пользователя"""
        if not self.user_manager.current_user:
            raise ValueError("Сначала выполните login")

        portfolio = self.user_manager.get_current_portfolio()
        if not portfolio:
            return {}, 0.0

        # Получение информации о кошельках
        wallets_info = {}
        for currency, wallet in portfolio.wallets.items():
            wallets_info[currency] = {
                "balance": wallet.balance,
                "value_in_base": self._convert_currency(
                    wallet.balance, currency, base_currency
                )
            }

        total_value = portfolio.get_total_value(base_currency)
        return wallets_info, total_value

    def buy_currency(self, currency_code: str, amount: float) -> Dict:
        """Покупка валюты"""
        if not self.user_manager.current_user:
            raise ValueError("Сначала выполните login")

        # Валидация
        currency_code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        portfolio = self.user_manager.get_current_portfolio()

        # Получение или создание кошелька
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            wallet = portfolio.add_currency(currency_code)

        # Пополнение кошелька
        wallet.deposit(amount)

        # Сохранение портфеля
        self.user_manager._save_portfolio(portfolio)

        # Расчет стоимости покупки
        cost_in_usd = self._convert_currency(amount, currency_code, "USD")

        return {
            "currency": currency_code,
            "amount": amount,
            "new_balance": wallet.balance,
            "cost_usd": cost_in_usd
        }

    def sell_currency(self, currency_code: str, amount: float) -> Dict:
        """Продажа валюты"""
        if not self.user_manager.current_user:
            raise ValueError("Сначала выполните login")

        # Валидация
        currency_code = validate_currency_code(currency_code)
        amount = validate_amount(amount)

        portfolio = self.user_manager.get_current_portfolio()

        # Получение кошелька
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            raise ValueError(f"У вас нет кошелька '{currency_code}'")

        # Проверка достаточности средств
        if amount > wallet.balance:
            raise ValueError(
                f"Недостаточно средств: доступно {wallet.balance} {currency_code}, "
                f"требуется {amount}"
            )

        # Снятие средств
        wallet.withdraw(amount)

        # Сохранение портфеля
        self.user_manager._save_portfolio(portfolio)

        # Расчет выручки
        revenue_in_usd = self._convert_currency(amount, currency_code, "USD")

        return {
            "currency": currency_code,
            "amount": amount,
            "new_balance": wallet.balance,
            "revenue_usd": revenue_in_usd
        }

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        """Получение курса валюты"""
        from_currency = validate_currency_code(from_currency)
        to_currency = validate_currency_code(to_currency)

        # Проверка существования курса
        rate_key = f"{from_currency}_{to_currency}"
        rates = self.exchange_rates.get("rates", {})

        if rate_key not in rates:
            # Попытка получить обратный курс
            reverse_key = f"{to_currency}_{from_currency}"
            if reverse_key in rates:
                rate = 1 / rates[reverse_key]["rate"]
                return {
                    "from": from_currency,
                    "to": to_currency,
                    "rate": rate,
                    "updated_at": rates[reverse_key]["updated_at"]
                }
            else:
                raise ValueError(f"Курс {from_currency}-{to_currency} недоступен")

        rate_data = rates[rate_key]
        return {
            "from": from_currency,
            "to": to_currency,
            "rate": rate_data["rate"],
            "updated_at": rate_data["updated_at"]
        }

    def _convert_currency(self, amount: float, from_currency: str, to_currency: str) -> float:
        """Конвертация валюты"""
        if from_currency == to_currency:
            return amount

        try:
            rate_data = self.get_exchange_rate(from_currency, to_currency)
            return amount * rate_data["rate"]
        except ValueError:
            return 0.0