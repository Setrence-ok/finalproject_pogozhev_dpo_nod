import json
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

from .exceptions import CurrencyNotFoundError, InsufficientFundsError
from .models import User, Wallet, Portfolio
from .utils import SessionManager
from ..infra.database import DatabaseManager
from ..decorators import log_action
from ..infra.settings import SettingsLoader
from .currencies import CurrencyRegistry


class UserUseCases:
    @staticmethod
    def register(username: str, password: str) -> User:
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        db = DatabaseManager()
        users = db.load_users()

        if any(u["username"] == username for u in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        user_id = max((u["user_id"] for u in users), default=0) + 1
        salt = User._User__generate_salt()
        hashed_password = User._User__hash_password(password, salt)

        user = User(
            user_id=user_id,
            username=username,
            hashed_password=hashed_password,
            salt=salt,
            registration_date=datetime.now()
        )

        users.append(user.to_dict())
        db.save_users(users)

        # Создаем пустой портфель
        portfolios = db.load_portfolios()
        portfolios.append({
            "user_id": user_id,
            "wallets": {}
        })
        db.save_portfolios(portfolios)

        return user

    @staticmethod
    def login(username: str, password: str) -> User:
        db = DatabaseManager()
        users = db.load_users()

        user_data = next((u for u in users if u["username"] == username), None)
        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        user = User.from_dict(user_data)

        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        SessionManager.login(user)
        return user


class PortfolioUseCases:
    @staticmethod
    def get_portfolio(user_id: int) -> Portfolio:
        db = DatabaseManager()
        portfolios = db.load_portfolios()

        portfolio_data = next((p for p in portfolios if p["user_id"] == user_id), None)
        if not portfolio_data:
            portfolio_data = {"user_id": user_id, "wallets": {}}
            portfolios.append(portfolio_data)
            db.save_portfolios(portfolios)

        return Portfolio.from_dict(portfolio_data)


    @staticmethod
    def save_portfolio(portfolio: Portfolio):
        db = DatabaseManager()
        portfolios = db.load_portfolios()

        for i, p in enumerate(portfolios):
            if p["user_id"] == portfolio.user_id:
                portfolios[i] = portfolio.to_dict()
                break
        else:
            portfolios.append(portfolio.to_dict())

        db.save_portfolios(portfolios)

    @staticmethod
    @log_action(action_name="BUY", verbose=True)
    def buy_currency(user_id: int, currency_code: str, amount: float) -> Tuple[Portfolio, float]:
        """Купить валюту"""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        # Валидация валюты через реестр
        try:
            currency = CurrencyRegistry.get_currency(currency_code.upper())
        except CurrencyNotFoundError:
            raise CurrencyNotFoundError(currency_code.upper())

        portfolio = PortfolioUseCases.get_portfolio(user_id)

        # Получаем курс из базы данных
        db = DatabaseManager()
        rates = db.load_rates()
        rate_key = f"{currency_code.upper()}_USD"

        # Проверяем актуальность курса
        settings = SettingsLoader()
        ttl_seconds = settings.get("RATES_TTL_SECONDS", 300)

        if rate_key not in rates.get("pairs", {}):
            raise ValueError(f"Не удалось получить курс для {currency_code}")

        rate_data = rates["pairs"][rate_key]
        updated_at = datetime.fromisoformat(rate_data["updated_at"])
        now = datetime.now()

        if (now - updated_at).total_seconds() > ttl_seconds:
            raise ValueError(f"Курс для {currency_code} устарел. Выполните 'update-rates'")

        rate = rate_data["rate"]

        # Получаем или создаем кошелек
        wallet = portfolio.get_wallet(currency_code.upper())
        if not wallet:
            wallet = portfolio.add_currency(currency_code.upper())

        wallet.deposit(amount)

        PortfolioUseCases.save_portfolio(portfolio)
        return portfolio, rate

    @staticmethod
    @log_action(action_name="SELL", verbose=True)
    def sell_currency(user_id: int, currency_code: str, amount: float) -> Tuple[Portfolio, float]:
        """Продать валюту"""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        # Валидация валюты через реестр
        try:
            currency = CurrencyRegistry.get_currency(currency_code.upper())
        except CurrencyNotFoundError:
            raise CurrencyNotFoundError(currency_code.upper())

        portfolio = PortfolioUseCases.get_portfolio(user_id)

        # Проверяем наличие кошелька
        wallet = portfolio.get_wallet(currency_code.upper())
        if not wallet:
            raise ValueError(f"У вас нет кошелька '{currency_code}'. "
                             f"Добавьте валюту: она создаётся автоматически при первой покупке.")

        # Проверяем достаточность средств
        if wallet.balance < amount:
            raise InsufficientFundsError(
                available=wallet.balance,
                required=amount,
                code=currency_code.upper()
            )

        # Получаем курс из базы данных
        db = DatabaseManager()
        rates = db.load_rates()
        rate_key = f"{currency_code.upper()}_USD"

        # Проверяем актуальность курса
        settings = SettingsLoader()
        ttl_seconds = settings.get("RATES_TTL_SECONDS", 300)

        if rate_key not in rates.get("pairs", {}):
            raise ValueError(f"Не удалось получить курс для {currency_code}")

        rate_data = rates["pairs"][rate_key]
        updated_at = datetime.fromisoformat(rate_data["updated_at"])
        now = datetime.now()

        if (now - updated_at).total_seconds() > ttl_seconds:
            raise ValueError(f"Курс для {currency_code} устарел. Выполните 'update-rates'")

        rate = rate_data["rate"]

        # Снимаем средства
        wallet.withdraw(amount)

        PortfolioUseCases.save_portfolio(portfolio)
        return portfolio, rate

    @staticmethod
    @log_action(action_name="SHOW_PORTFOLIO", verbose=False)
    def get_portfolio_with_rates(user_id: int, base_currency: str = 'USD') -> Tuple[Portfolio, dict]:
        """Получить портфель с актуальными курсами"""
        portfolio = PortfolioUseCases.get_portfolio(user_id)

        db = DatabaseManager()
        rates = db.load_rates()

        # Конвертируем курсы в нужную валюту
        converted_rates = {}
        for pair, rate_data in rates.get("pairs", {}).items():
            if pair.endswith(f"_{base_currency}"):
                currency = pair.replace(f"_{base_currency}", "")
                converted_rates[currency] = rate_data["rate"]

        return portfolio, converted_rates


class RatesUseCases:
    @staticmethod
    def get_rate(from_currency: str, to_currency: str) -> Tuple[float, str]:
        db = DatabaseManager()
        rates = db.load_rates()

        pair_key = f"{from_currency}_{to_currency}"

        if pair_key not in rates.get("pairs", {}):
            # Пробуем обратный курс
            reverse_key = f"{to_currency}_{from_currency}"
            if reverse_key in rates.get("pairs", {}):
                rate = 1 / rates["pairs"][reverse_key]["rate"]
                updated_at = rates["pairs"][reverse_key]["updated_at"]
                return rate, updated_at
            else:
                raise ValueError(f"Курс {from_currency}={to_currency} недоступен")

        rate_data = rates["pairs"][pair_key]
        return rate_data["rate"], rate_data["updated_at"]