import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("parser.config")


@dataclass
class ParserConfig:
    """
    Конфигурация для парсер-сервиса.
    Все настройки централизованы здесь.
    """

    # API ключи (загружаются из переменных окружения)
    EXCHANGERATE_API_KEY: str = field(default_factory=lambda: os.getenv(
        "EXCHANGERATE_API_KEY",
        "demo_key_for_testing"
    ))

    # Проверка ключа
    @property
    def has_valid_exchangerate_key(self) -> bool:
        """Проверяет, является ли ключ демо-ключом"""
        return self.EXCHANGERATE_API_KEY not in ["demo_key_for_testing", "", None]

    # Эндпоинты API
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Базовая валюта для запросов
    BASE_CURRENCY: str = "USD"

    # Списки отслеживаемых валют
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "JPY", "CNY", "RUB", "CHF", "CAD", "AUD")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "LTC", "DOGE", "ADA", "DOT", "SOL", "XRP")

    # Сопоставление кодов криптовалют с ID CoinGecko
    CRYPTO_ID_MAP: Dict[str, str] = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "DOGE": "dogecoin",
        "ADA": "cardano",
        "DOT": "polkadot",
        "SOL": "solana",
        "XRP": "ripple",
        "BNB": "binancecoin",
        "USDT": "tether",
        "USDC": "usd-coin",
    })

    # Сетевые параметры
    REQUEST_TIMEOUT: int = 15
    REQUEST_RETRIES: int = 3
    RETRY_DELAY: float = 2.0

    # Пути к файлам
    DATA_DIR: Path = field(default_factory=lambda: Path("data"))
    RATES_FILE_PATH: Path = field(init=False)
    HISTORY_FILE_PATH: Path = field(init=False)

    # TTL для кэша (в секундах)
    CACHE_TTL_SECONDS: int = 300  # 5 минут

    # Логирование
    LOG_DIR: Path = field(default_factory=lambda: Path("logs"))
    PARSER_LOG_FILE: Path = field(init=False)

    # Планировщик
    SCHEDULER_ENABLED: bool = False  # По умолчанию выключен
    SCHEDULER_INTERVAL_MINUTES: int = 15

    def __post_init__(self):
        """Инициализация вычисляемых полей"""
        # Инициализируем пути
        self.RATES_FILE_PATH = self.DATA_DIR / "rates.json"
        self.HISTORY_FILE_PATH = self.DATA_DIR / "exchange_rates.json"
        self.PARSER_LOG_FILE = self.LOG_DIR / "parser.log"

        # Создаем директории, если их нет
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOG_DIR.mkdir(exist_ok=True)

        # Логируем статус API ключа
        if not self.has_valid_exchangerate_key:
            logger.warning(
                "ExchangeRate-API key is not set or using demo key. "
                "Fiat currency rates may be limited. "
                "Set EXCHANGERATE_API_KEY environment variable."
            )
        else:
            logger.info("ExchangeRate-API key is configured")

    @property
    def coingecko_params(self) -> Dict[str, str]:
        """Параметры для запроса к CoinGecko"""
        crypto_ids = [
            self.CRYPTO_ID_MAP.get(c, c.lower())
            for c in self.CRYPTO_CURRENCIES
            if c in self.CRYPTO_ID_MAP
        ]
        return {
            "ids": ",".join(crypto_ids),
            "vs_currencies": self.BASE_CURRENCY.lower(),
            "precision": "full"
        }

    @property
    def exchangerate_api_url(self) -> str:
        """URL для запроса к ExchangeRate-API"""
        return f"{self.EXCHANGERATE_API_URL}/{self.EXCHANGERATE_API_KEY}/latest/{self.BASE_CURRENCY}"

    def get_crypto_id(self, currency_code: str) -> Optional[str]:
        """Получение ID криптовалюты по коду"""
        return self.CRYPTO_ID_MAP.get(currency_code.upper())

    def is_crypto_currency(self, currency_code: str) -> bool:
        """Проверка, является ли валюта криптовалютой"""
        return currency_code.upper() in self.CRYPTO_CURRENCIES

    def is_fiat_currency(self, currency_code: str) -> bool:
        """Проверка, является ли валюта фиатной"""
        return currency_code.upper() in self.FIAT_CURRENCIES


# Глобальный экземпляр конфигурации
config = ParserConfig()