import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..core.exceptions import ApiRequestError
from .config import config

logger = logging.getLogger("parser.api")


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ValutaTradeHub/1.0 (Educational Project)"
        })

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов валют от API.

        Returns:
            Словарь с курсами в формате { "BTC_USD": 59337.21, ... }

        Raises:
            ApiRequestError: при ошибках сети или API
        """
        pass

    def _make_request(self, url: str, params: Optional[Dict] = None,
                      method: str = "GET") -> Dict[str, Any]:
        """
        Выполнение HTTP запроса с обработкой ошибок и retry логикой.

        Args:
            url: URL для запроса
            params: Параметры запроса
            method: HTTP метод

        Returns:
            Ответ API в виде словаря

        Raises:
            ApiRequestError: при ошибках
        """
        last_exception = None

        for attempt in range(config.REQUEST_RETRIES):
            try:
                logger.debug(f"[{self.name}] Attempt {attempt + 1}/{config.REQUEST_RETRIES} to {url}")

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=config.REQUEST_TIMEOUT
                )

                # Проверка статуса ответа
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"[{self.name}] Rate limit exceeded. Retrying after {retry_after} seconds")
                    if attempt < config.REQUEST_RETRIES - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise ApiRequestError(f"Rate limit exceeded after {config.REQUEST_RETRIES} attempts")
                elif response.status_code == 401:  # Unauthorized
                    raise ApiRequestError("Invalid API key or unauthorized access")
                elif response.status_code == 403:  # Forbidden
                    raise ApiRequestError("Access forbidden. Check API key permissions")
                else:
                    raise ApiRequestError(f"API returned status {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                last_exception = ApiRequestError(f"Request timeout for {self.name}")
                logger.warning(f"[{self.name}] Timeout on attempt {attempt + 1}")
            except requests.exceptions.ConnectionError:
                last_exception = ApiRequestError(f"Connection error for {self.name}")
                logger.warning(f"[{self.name}] Connection error on attempt {attempt + 1}")
            except requests.exceptions.RequestException as e:
                last_exception = ApiRequestError(f"Request failed: {str(e)}")
                logger.warning(f"[{self.name}] Request failed on attempt {attempt + 1}: {e}")

            # Задержка перед повторной попыткой
            if attempt < config.REQUEST_RETRIES - 1:
                time.sleep(config.RETRY_DELAY)

        # Если все попытки провалились
        raise last_exception if last_exception else ApiRequestError("Unknown error")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', url='{self.base_url}')"


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API (криптовалюты)"""

    def __init__(self):
        super().__init__(
            name="CoinGecko",
            base_url=config.COINGECKO_URL
        )

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов криптовалют от CoinGecko.

        Returns:
            Словарь курсов в формате { "BTC_USD": 59337.21, ... }
        """
        logger.info(f"[{self.name}] Fetching cryptocurrency rates")

        try:
            # Выполняем запрос
            data = self._make_request(
                url=self.base_url,
                params=config.coingecko_params
            )

            # Преобразуем ответ в унифицированный формат
            rates = {}
            for crypto_id, rates_dict in data.items():
                # Находим код валюты по ID
                currency_code = None
                for code, cg_id in config.CRYPTO_ID_MAP.items():
                    if cg_id == crypto_id:
                        currency_code = code
                        break

                if currency_code and "usd" in rates_dict:
                    rate_key = f"{currency_code}_{config.BASE_CURRENCY}"
                    rates[rate_key] = float(rates_dict["usd"])

            logger.info(f"[{self.name}] Fetched {len(rates)} cryptocurrency rates")
            return rates

        except Exception as e:
            logger.error(f"[{self.name}] Failed to fetch rates: {e}")
            raise

    def fetch_single_rate(self, currency_code: str) -> Optional[float]:
        """
        Получение курса одной криптовалюты.

        Args:
            currency_code: Код криптовалюты

        Returns:
            Курс к USD или None, если не найден
        """
        crypto_id = config.get_crypto_id(currency_code)
        if not crypto_id:
            return None

        params = {
            "ids": crypto_id,
            "vs_currencies": "usd",
            "precision": "full"
        }

        try:
            data = self._make_request(url=self.base_url, params=params)
            if crypto_id in data and "usd" in data[crypto_id]:
                return float(data[crypto_id]["usd"])
        except Exception:
            pass

        return None


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API (фиатные валюты)"""

    def __init__(self):
        super().__init__(
            name="ExchangeRate-API",
            base_url=config.EXCHANGERATE_API_URL
        )
        self.api_key = config.EXCHANGERATE_API_KEY

    def fetch_rates(self) -> Dict[str, float]:
        """
        Получение курсов фиатных валют от ExchangeRate-API.

        Returns:
            Словарь курсов в формате { "EUR_USD": 1.0786, ... }
        """
        logger.info(f"[{self.name}] Fetching fiat currency rates")

        try:
            # Выполняем запрос
            url = config.exchangerate_api_url
            data = self._make_request(url=url)

            # Проверяем успешность ответа
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(f"API returned error: {error_type}")

            # Преобразуем ответ в унифицированный формат
            rates = {}
            base_currency = data.get("base_code", config.BASE_CURRENCY)
            rates_dict = data.get("conversion_rates", {}) or data.get("rates", {})

            for currency_code, rate in rates_dict.items():
                # Пропускаем базовую валюту (курс к самому себе = 1)
                if currency_code == base_currency:
                    continue

                # Проверяем, что валюта в нашем списке отслеживаемых
                if currency_code in config.FIAT_CURRENCIES:
                    rate_key = f"{currency_code}_{base_currency}"
                    rates[rate_key] = float(rate)

            logger.info(f"[{self.name}] Fetched {len(rates)} fiat currency rates")
            return rates

        except Exception as e:
            logger.error(f"[{self.name}] Failed to fetch rates: {e}")
            raise

    def fetch_single_rate(self, from_currency: str, to_currency: str = None) -> Optional[float]:
        """
        Получение курса одной фиатной валюты.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта (по умолчанию USD)

        Returns:
            Курс или None, если не найден
        """
        to_currency = to_currency or config.BASE_CURRENCY

        if from_currency == to_currency:
            return 1.0

        url = f"{self.base_url}/{self.api_key}/pair/{from_currency}/{to_currency}"

        try:
            data = self._make_request(url=url)
            if data.get("result") == "success":
                return float(data.get("conversion_rate", 0))
        except Exception:
            pass

        return None


class MockApiClient(BaseApiClient):
    """Mock клиент для тестирования (использует фиксированные значения)"""

    def __init__(self):
        super().__init__(
            name="MockAPI",
            base_url="mock://api.example.com"
        )
        self._mock_rates = {
            "BTC_USD": 59337.21,
            "ETH_USD": 3720.00,
            "LTC_USD": 75.50,
            "EUR_USD": 1.0786,
            "GBP_USD": 1.235,
            "RUB_USD": 0.01016,
        }

    def fetch_rates(self) -> Dict[str, float]:
        """
        Возвращает фиксированные курсы для тестирования.
        Имитирует задержку сети.
        """
        logger.info(f"[{self.name}] Returning mock rates for testing")
        time.sleep(0.5)  # Имитация задержки сети
        return self._mock_rates.copy()


def create_api_client(source: str = None) -> BaseApiClient:
    """
    Фабрика для создания API клиентов.

    Args:
        source: Источник данных ("coingecko", "exchangerate", "mock", "all")
               Если None или "all", возвращает список всех клиентов

    Returns:
        API клиент или список клиентов
    """
    clients = []

    if source in [None, "all", "coingecko"]:
        clients.append(CoinGeckoClient())

    if source in [None, "all", "exchangerate"]:
        # Проверяем, есть ли API ключ (кроме демо-ключа)
        if config.EXCHANGERATE_API_KEY != "demo_key_for_testing":
            clients.append(ExchangeRateApiClient())
        else:
            logger.warning("ExchangeRate-API key not set. Using mock data instead.")
            clients.append(MockApiClient())

    if source == "mock":
        clients.append(MockApiClient())

    # Если запросили конкретный источник, но он не доступен
    if source in ["coingecko", "exchangerate"] and not clients:
        raise ValueError(f"Source '{source}' is not available")

    return clients if len(clients) != 1 else clients[0]