from abc import ABC, abstractmethod
from typing import Dict
from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    def __init__(self, name: str, code: str):
        if not name or not name.strip():
            raise ValueError("Название валюты не может быть пустым")
        if not (2 <= len(code) <= 5) or not code.isalpha():
            raise ValueError("Код валюты должен содержать 2-5 буквенных символов")

        self.__name = name.strip()
        self.__code = code.upper()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def code(self) -> str:
        return self.__code

    @abstractmethod
    def get_display_info(self) -> str:
        pass

    def __str__(self) -> str:
        return f"{self.__code} - {self.__name}"


class FiatCurrency(Currency):
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.__issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        return self.__issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.__issuing_country})"


class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self.__algorithm = algorithm
        self.__market_cap = market_cap

    @property
    def algorithm(self) -> str:
        return self.__algorithm

    @property
    def market_cap(self) -> float:
        return self.__market_cap

    def get_display_info(self) -> str:
        mcap_str = f"{self.__market_cap:.2e}" if self.__market_cap > 1e6 else f"{self.__market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.__algorithm}, MCAP: {mcap_str})"


# Реестр валют (фабрика)
class CurrencyRegistry:
    _currencies: Dict[str, Currency] = {}

    @classmethod
    def initialize(cls):
        """Инициализация реестра валют"""
        if not cls._currencies:
            # Фиатные валюты
            cls._currencies["USD"] = FiatCurrency("US Dollar", "USD", "United States")
            cls._currencies["EUR"] = FiatCurrency("Euro", "EUR", "Eurozone")
            cls._currencies["RUB"] = FiatCurrency("Russian Ruble", "RUB", "Russia")
            cls._currencies["GBP"] = FiatCurrency("British Pound", "GBP", "United Kingdom")

            # Криптовалюты
            cls._currencies["BTC"] = CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12)
            cls._currencies["ETH"] = CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11)
            cls._currencies["SOL"] = CryptoCurrency("Solana", "SOL", "Proof of History", 6.7e10)

    @classmethod
    def get_currency(cls, code: str) -> Currency:
        """Получить валюту по коду"""
        cls.initialize()
        currency = cls._currencies.get(code.upper())
        if not currency:
            raise CurrencyNotFoundError(code.upper())
        return currency

    @classmethod
    def get_all_codes(cls) -> list:
        """Получить все коды валют"""
        cls.initialize()
        return list(cls._currencies.keys())