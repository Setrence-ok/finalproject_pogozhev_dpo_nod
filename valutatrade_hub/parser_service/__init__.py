"""
Parser Service для ValutaTrade Hub.

Этот модуль предоставляет функциональность для получения
актуальных курсов валют из внешних API.
"""

from .config import config, ParserConfig
from .api_clients import (
    BaseApiClient,
    CoinGeckoClient,
    ExchangeRateApiClient,
    MockApiClient,
    create_api_client,
)
from .storage import storage, RatesStorage
from .updater import updater, RatesUpdater
from .scheduler import scheduler, RatesScheduler

__all__ = [
    # Конфигурация
    "config",
    "ParserConfig",

    # API клиенты
    "BaseApiClient",
    "CoinGeckoClient",
    "ExchangeRateApiClient",
    "MockApiClient",
    "create_api_client",

    # Хранилище
    "storage",
    "RatesStorage",

    # Обновление
    "updater",
    "RatesUpdater",

    # Планировщик
    "scheduler",
    "RatesScheduler",
]

__version__ = "1.0.0"