import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .api_clients import create_api_client, BaseApiClient
from .storage import storage
from .config import config
from ..core.exceptions import ApiRequestError

logger = logging.getLogger("parser.updater")


class RatesUpdater:
    """
    Класс для координации процесса обновления курсов.
    Управляет запросами к API, объединением данных и сохранением.
    """

    def __init__(self, clients: Optional[List[BaseApiClient]] = None):
        """
        Инициализация обновлятеля.

        Args:
            clients: Список API клиентов. Если None, создаются все доступные клиенты.
        """
        self.clients = clients or create_api_client("all")
        self.storage = storage

        if not isinstance(self.clients, list):
            self.clients = [self.clients]

    def run_update(self, source: str = None) -> Dict[str, Any]:
        """
        Запуск обновления курсов.

        Args:
            source: Источник для обновления ("coingecko", "exchangerate", "mock")
                   Если None, обновляются все источники.

        Returns:
            Результат обновления со статистикой
        """
        logger.info("=" * 60)
        logger.info("Starting rates update")
        logger.info(f"Sources: {source or 'all'}")
        logger.info("=" * 60)

        # Создаем клиенты для указанного источника
        update_clients = self.clients
        if source:
            update_clients = create_api_client(source)
            if not isinstance(update_clients, list):
                update_clients = [update_clients]

        all_rates = {}
        statistics = {
            "started_at": datetime.now().isoformat(),
            "sources": {},
            "total_rates": 0,
            "errors": [],
        }

        # Опрашиваем каждый источник
        for client in update_clients:
            source_name = client.name
            logger.info(f"Fetching rates from {source_name}...")

            try:
                # Получаем курсы от клиента
                rates = client.fetch_rates()

                # Объединяем с общим словарем
                # (новые значения перезаписывают старые)
                all_rates.update(rates)

                # Сохраняем статистику
                statistics["sources"][source_name] = {
                    "status": "success",
                    "rates_count": len(rates),
                    "rates": list(rates.keys())[:5]  # Первые 5 для примера
                }

                logger.info(f"✓ {source_name}: {len(rates)} rates fetched successfully")

            except ApiRequestError as e:
                error_msg = f"Failed to fetch from {source_name}: {e}"
                logger.error(error_msg)

                statistics["sources"][source_name] = {
                    "status": "error",
                    "error": str(e),
                    "rates_count": 0,
                }
                statistics["errors"].append(error_msg)

            except Exception as e:
                error_msg = f"Unexpected error from {source_name}: {e}"
                logger.exception(error_msg)

                statistics["sources"][source_name] = {
                    "status": "error",
                    "error": str(e),
                    "rates_count": 0,
                }
                statistics["errors"].append(error_msg)

        # Сохраняем данные, если что-то получили
        if all_rates:
            # Определяем основной источник (первый успешный или общий)
            main_source = "mixed"
            for source_name, stat in statistics["sources"].items():
                if stat.get("status") == "success":
                    main_source = source_name
                    break

            # Подготавливаем метаданные
            meta = {
                "update_id": f"update_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "statistics": statistics,
                "config": {
                    "base_currency": config.BASE_CURRENCY,
                    "fiat_currencies": config.FIAT_CURRENCIES,
                    "crypto_currencies": config.CRYPTO_CURRENCIES,
                }
            }

            # Сохраняем в кэш
            cache_result = self.storage.save_current_rates(
                rates=all_rates,
                source=main_source,
                meta=meta
            )

            # Сохраняем в историю
            history_result = self.storage.save_to_history(
                rates=all_rates,
                source=main_source,
                meta=meta
            )

            statistics["total_rates"] = len(all_rates)
            statistics["saved_to_cache"] = len(cache_result.get("pairs", {}))
            statistics["saved_to_history"] = len(history_result)
            statistics["last_refresh"] = cache_result.get("last_refresh")

            logger.info(f"Update completed: {len(all_rates)} rates saved")

        else:
            logger.warning("Update completed with no rates fetched")
            statistics["total_rates"] = 0

        statistics["completed_at"] = datetime.now().isoformat()
        statistics["success"] = len(all_rates) > 0

        logger.info("=" * 60)
        logger.info(f"Update completed: {'SUCCESS' if statistics['success'] else 'NO DATA'}")
        logger.info(f"Total rates: {statistics['total_rates']}")
        logger.info(f"Errors: {len(statistics['errors'])}")
        logger.info("=" * 60)

        return statistics

    def update_if_stale(self) -> Dict[str, Any]:
        """
        Обновление курсов, только если кэш устарел.

        Returns:
            Результат обновления или информация о свежем кэше
        """
        if self.storage.is_cache_fresh():
            logger.info("Cache is fresh, skipping update")
            return {
                "updated": False,
                "reason": "cache_fresh",
                "cache_age": "fresh",
                "rates_count": len(self.storage.load_current_rates().get("pairs", {})),
            }
        else:
            logger.info("Cache is stale, performing update")
            return {
                "updated": True,
                **self.run_update()
            }

    def force_update(self) -> Dict[str, Any]:
        """
        Принудительное обновление курсов (игнорируя свежесть кэша).

        Returns:
            Результат обновления
        """
        logger.info("Forcing rates update (ignoring cache freshness)")
        return self.run_update()


# Глобальный экземпляр обновлятеля
updater = RatesUpdater()