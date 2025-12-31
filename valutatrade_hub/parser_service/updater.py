import logging

from .config import ParserConfig
from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .storage import RatesStorage
from ..core.exceptions import ApiRequestError


class RatesUpdater:
    """Основной класс для обновления курсов"""

    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()
        self.storage = RatesStorage(self.config)
        self.logger = logging.getLogger('valutatrade.parser')

    def run_update(self, source: str = None) -> int:
        """Запустить обновление курсов"""
        self.logger.info("Starting rates update...")

        all_rates = {}
        errors = []

        # Обрабатываем CoinGecko
        if not source or source.lower() == 'coingecko':
            try:
                self.logger.info("Fetching from CoinGecko...")
                client = CoinGeckoClient(self.config)
                rates = client.fetch_rates()
                all_rates.update(rates)
                self.logger.info(f"CoinGecko OK ({len(rates)} rates)")
            except ApiRequestError as e:
                error_msg = f"Failed to fetch from CoinGecko: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Обрабатываем ExchangeRate-API
        if not source or source.lower() == 'exchangerate':
            try:
                self.logger.info("Fetching from ExchangeRate-API...")
                client = ExchangeRateApiClient(self.config)
                rates = client.fetch_rates()
                all_rates.update(rates)
                self.logger.info(f"ExchangeRate-API OK ({len(rates)} rates)")
            except ApiRequestError as e:
                error_msg = f"Failed to fetch from ExchangeRate-API: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        # Сохраняем результаты
        if all_rates:
            try:
                self.logger.info(f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}...")
                self.storage.save_current_rates(all_rates, "ParserService")
                self.storage.save_to_history(all_rates, "ParserService")

                if errors:
                    self.logger.warning(f"Update completed with {len(errors)} errors")
                    return len(all_rates)
                else:
                    self.logger.info(f"Update successful. Total rates updated: {len(all_rates)}")
                    return len(all_rates)

            except Exception as e:
                error_msg = f"Failed to save rates: {str(e)}"
                self.logger.error(error_msg)
                errors.append(error_msg)
                return 0
        else:
            self.logger.error("No rates were fetched")
            return 0