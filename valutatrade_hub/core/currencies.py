from abc import ABC, abstractmethod
from typing import Dict, Optional


class Currency(ABC):
    """Абстрактный базовый класс для всех валют"""

    def __init__(self, name: str, code: str):
        self._name = name
        self._code = self._validate_code(code)

    @property
    def name(self) -> str:
        return self._name

    @property
    def code(self) -> str:
        return self._code

    def _validate_code(self, code: str) -> str:
        """Валидация кода валюты"""
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты должен быть непустой строкой")

        code = code.upper().strip()
        if not 2 <= len(code) <= 5:
            raise ValueError("Код валюты должен содержать 2-5 символов")
        if ' ' in code:
            raise ValueError("Код валюты не должен содержать пробелов")

        return code

    @abstractmethod
    def get_display_info(self) -> str:
        """Абстрактный метод для получения информации о валюте"""
        pass

    def __str__(self) -> str:
        return self.get_display_info()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', code='{self.code}')"


class FiatCurrency(Currency):
    """Фиатная валюта (обычные государственные валюты)"""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        return self._issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class Cryptocurrency(Currency):
    """Криптовалюта"""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self._algorithm = algorithm
        self._market_cap = market_cap

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def market_cap(self) -> float:
        return self._market_cap

    def get_display_info(self) -> str:
        # Форматируем капитализацию для читаемости
        if self._market_cap >= 1e12:
            cap_str = f"{self._market_cap / 1e12:.2f}T"
        elif self._market_cap >= 1e9:
            cap_str = f"{self._market_cap / 1e9:.2f}B"
        elif self._market_cap >= 1e6:
            cap_str = f"{self._market_cap / 1e6:.2f}M"
        else:
            cap_str = f"{self._market_cap:,.2f}"

        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {cap_str})"



class CurrencyRegistry:
    """Реестр валют с фабричным методом"""

    # Предопределённые валюты
    _currencies: Dict[str, Currency] = {
        # Фиатные валюты
        "USD": FiatCurrency("US Dollar", "USD", "United States"),
        "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
        "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
        "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
        "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
        "CNY": FiatCurrency("Chinese Yuan", "CNY", "China"),

        # Криптовалюты
        "BTC": Cryptocurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
        "ETH": Cryptocurrency("Ethereum", "ETH", "Ethash", 450e9),
        "LTC": Cryptocurrency("Litecoin", "LTC", "Scrypt", 5.8e9),
        "DOGE": Cryptocurrency("Dogecoin", "DOGE", "Scrypt", 12.5e9),
    }

    @classmethod
    def get_currency(cls, code: str) -> Currency:
        """Фабричный метод для получения валюты по коду"""
        code = code.upper().strip()

        if code not in cls._currencies:
            # Динамическое создание валюты, если не найдена в реестре
            # (опционально - можно выбрасывать исключение)
            raise CurrencyNotFoundError(f"Неизвестная валюта '{code}'")

        return cls._currencies[code]

    @classmethod
    def register_currency(cls, currency: Currency) -> None:
        """Регистрация новой валюты в реестре"""
        cls._currencies[currency.code] = currency

    @classmethod
    def list_currencies(cls, currency_type: Optional[str] = None) -> Dict[str, Currency]:
        """Получение списка валют по типу"""
        if currency_type == "fiat":
            return {code: curr for code, curr in cls._currencies.items()
                    if isinstance(curr, FiatCurrency)}
        elif currency_type == "crypto":
            return {code: curr for code, curr in cls._currencies.items()
                    if isinstance(curr, Cryptocurrency)}
        else:
            return cls._currencies.copy()

    @classmethod
    def get_supported_codes(cls) -> list:
        """Получение списка поддерживаемых кодов валют"""
        return list(cls._currencies.keys())