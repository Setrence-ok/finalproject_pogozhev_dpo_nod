"""Основная бизнес-логика приложения"""
from datetime import datetime

from .models import User, Wallet, Portfolio
from .currencies import Currency, FiatCurrency, CryptoCurrency, CurrencyRegistry
from .exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
from .utils import SessionManager
from .usecases import UserUseCases, PortfolioUseCases, RatesUseCases

__all__ = [
    'User',
    'Wallet',
    'Portfolio',
    'Currency',
    'FiatCurrency',
    'CryptoCurrency',
    'CurrencyRegistry',
    'InsufficientFundsError',
    'CurrencyNotFoundError',
    'ApiRequestError',
    'SessionManager',
    'UserUseCases',
    'PortfolioUseCases',
    'RatesUseCases',
]

def __init__(self, user_id: int, username: str, hashed_password: str,
             salt: str, registration_date: datetime):
    self.__user_id = user_id
    self.username = username  # Используем сеттер для валидации
    self.__hashed_password = hashed_password
    self.__salt = salt
    self.__registration_date = registration_date