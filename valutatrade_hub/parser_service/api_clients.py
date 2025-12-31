import requests
from abc import ABC, abstractmethod
from typing import Dict
import time

from ..core.exceptions import ApiRequestError
from .config import ParserConfig


class BaseApiClient(ABC):
    """Базовый класс API клиента"""

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы валют"""
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API"""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> Dict[str, float]:
        try:
            # Формируем список ID криптовалют
            crypto_ids = []
            for code in self.config.CRYPTO_CURRENCIES:
                if code in self.config.CRYPTO_ID_MAP:
                    crypto_ids.append(self.config.CRYPTO_ID_MAP[code])

            if not crypto_ids:
                return {}

            # Формируем параметры запроса
            params = {
                'ids': ','.join(crypto_ids),
                'vs_currencies': self.config.BASE_CURRENCY.lower()
            }

            # Отправляем запрос
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )

            # Проверяем статус
            if response.status_code != 200:
                raise ApiRequestError(f"CoinGecko API error: {response.status_code}")

            data = response.json()

            # Преобразуем в нужный формат
            rates = {}
            for code in self.config.CRYPTO_CURRENCIES:
                if code in self.config.CRYPTO_ID_MAP:
                    coin_id = self.config.CRYPTO_ID_MAP[code]
                    if coin_id in data:
                        rate = data[coin_id].get(self.config.BASE_CURRENCY.lower())
                        if rate:
                            rates[f"{code}_{self.config.BASE_CURRENCY}"] = rate

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko network error: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API"""

    def __init__(self, config: ParserConfig):
        self.config = config

    def fetch_rates(self) -> Dict[str, float]:
        try:
            # Отправляем запрос
            response = requests.get(
                self.config.exchangerate_api_url,
                timeout=self.config.REQUEST_TIMEOUT
            )

            # Проверяем статус
            if response.status_code != 200:
                raise ApiRequestError(f"ExchangeRate-API error: {response.status_code}")

            data = response.json()

            if data.get('result') != 'success':
                raise ApiRequestError(f"ExchangeRate-API error: {data.get('error-type', 'Unknown error')}")

            # Преобразуем в нужный формат
            rates = {}
            base = data.get('base_code', 'USD')

            for target_currency in self.config.FIAT_CURRENCIES:
                if target_currency in data.get('rates', {}):
                    rate = data['rates'][target_currency]
                    # Конвертируем в формат target_BASE
                    if target_currency != base:
                        rates[f"{target_currency}_{base}"] = 1 / rate if rate != 0 else 0

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API network error: {str(e)}")