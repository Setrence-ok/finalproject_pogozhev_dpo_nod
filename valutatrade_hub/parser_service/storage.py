import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .config import config

logger = logging.getLogger("parser.storage")


class RatesStorage:
    """Класс для работы с хранилищем курсов валют"""

    def __init__(self):
        self.rates_file = config.RATES_FILE_PATH
        self.history_file = config.HISTORY_FILE_PATH

    def save_current_rates(self, rates: Dict[str, float], source: str,
                           meta: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Сохранение текущих курсов в rates.json (кеш).

        Args:
            rates: Словарь курсов в формате { "BTC_USD": 59337.21, ... }
            source: Источник данных
            meta: Дополнительные метаданные

        Returns:
            Сохраненные данные
        """
        timestamp = datetime.now().isoformat()

        # Подготавливаем данные для сохранения
        pairs_data = {}
        for pair_key, rate in rates.items():
            # Разделяем пару валют
            if "_" in pair_key:
                from_curr, to_curr = pair_key.split("_", 1)
            else:
                from_curr, to_curr = pair_key, config.BASE_CURRENCY

            pairs_data[pair_key] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source,
                "from_currency": from_curr,
                "to_currency": to_curr,
            }

        # Формируем полную структуру данных
        data = {
            "last_refresh": timestamp,
            "source": source,
            "pairs": pairs_data,
            "meta": meta or {},
        }

        # Атомарная запись (через временный файл)
        self._atomic_write(self.rates_file, data)

        logger.info(f"Saved {len(rates)} rates to {self.rates_file}")
        return data

    def save_to_history(self, rates: Dict[str, float], source: str,
                        meta: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Сохранение курсов в историю (exchange_rates.json).
        Каждый курс сохраняется как отдельная запись с уникальным ID.

        Args:
            rates: Словарь курсов
            source: Источник данных
            meta: Дополнительные метаданные

        Returns:
            Список сохраненных записей
        """
        timestamp = datetime.now().isoformat()
        saved_records = []

        # Загружаем существующую историю
        history = self._load_history()

        for pair_key, rate in rates.items():
            # Разделяем пару валют
            if "_" in pair_key:
                from_curr, to_curr = pair_key.split("_", 1)
            else:
                from_curr, to_curr = pair_key, config.BASE_CURRENCY

            # Создаем уникальный ID
            record_id = f"{pair_key}_{timestamp.replace(':', '-').replace('.', '-')}"

            record = {
                "id": record_id,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": {
                    "raw_pair": pair_key,
                    **(meta or {})
                }
            }

            # Добавляем запись в историю
            history.append(record)
            saved_records.append(record)

        # Сохраняем обновленную историю
        self._atomic_write(self.history_file, history)

        logger.info(f"Saved {len(rates)} records to history")
        return saved_records

    def load_current_rates(self) -> Dict[str, Any]:
        """
        Загрузка текущих курсов из кэша.

        Returns:
            Данные из rates.json или пустой словарь, если файл не существует
        """
        return self._load_json(self.rates_file, default={"pairs": {}, "last_refresh": None})

    def load_history(self, limit: int = None, currency: str = None) -> List[Dict[str, Any]]:
        """
        Загрузка истории курсов с фильтрацией.

        Args:
            limit: Ограничение количества записей
            currency: Фильтр по валюте (ищет в from_currency и to_currency)

        Returns:
            Список исторических записей
        """
        history = self._load_history()

        # Применяем фильтры
        if currency:
            currency = currency.upper()
            history = [
                record for record in history
                if (record.get("from_currency") == currency or
                    record.get("to_currency") == currency)
            ]

        # Сортируем по времени (новые сначала)
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Применяем лимит
        if limit:
            history = history[:limit]

        return history

    def is_cache_fresh(self) -> bool:
        """
        Проверка свежести кэша.

        Returns:
            True, если данные в кэше свежие (не старше TTL)
        """
        data = self.load_current_rates()
        last_refresh = data.get("last_refresh")

        if not last_refresh:
            return False

        try:
            last_update = datetime.fromisoformat(last_refresh)
            now = datetime.now()
            age_seconds = (now - last_update).total_seconds()

            return age_seconds <= config.CACHE_TTL_SECONDS
        except (ValueError, TypeError):
            return False

    def get_rate(self, from_currency: str, to_currency: str = None) -> Optional[float]:
        """
        Получение курса из кэша.

        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта (по умолчанию BASE_CURRENCY)

        Returns:
            Курс или None, если не найден
        """
        to_currency = to_currency or config.BASE_CURRENCY

        if from_currency == to_currency:
            return 1.0

        data = self.load_current_rates()
        pairs = data.get("pairs", {})

        # Прямой поиск
        pair_key = f"{from_currency}_{to_currency}"
        if pair_key in pairs:
            return pairs[pair_key].get("rate")

        # Поиск обратного курса
        reverse_key = f"{to_currency}_{from_currency}"
        if reverse_key in pairs:
            rate = pairs[reverse_key].get("rate")
            return 1 / rate if rate != 0 else None

        return None

    def _load_history(self) -> List[Dict[str, Any]]:
        """Загрузка истории из файла"""
        return self._load_json(self.history_file, default=[])

    def _load_json(self, filepath: Path, default: Any = None) -> Any:
        """Загрузка JSON файла"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            logger.warning(f"Failed to load {filepath}: {e}")

        return default if default is not None else {}

    def _atomic_write(self, filepath: Path, data: Any) -> None:
        """
        Атомарная запись в JSON файл (через временный файл).

        Args:
            filepath: Путь к файлу
            data: Данные для записи
        """
        # Создаем временный файл
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.tmp',
            prefix=filepath.stem,
            dir=filepath.parent
        )

        try:
            # Пишем данные во временный файл
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

            # Атомарно заменяем оригинальный файл
            Path(temp_path).replace(filepath)

        except Exception as e:
            # Удаляем временный файл при ошибке
            try:
                Path(temp_path).unlink()
            except OSError:
                pass
            raise IOError(f"Failed to write {filepath}: {e}")

    def clear_cache(self) -> None:
        """Очистка кэша курсов"""
        if self.rates_file.exists():
            self.rates_file.unlink()
            logger.info("Cleared rates cache")

    def clear_history(self) -> None:
        """Очистка истории курсов"""
        if self.history_file.exists():
            self.history_file.unlink()
            logger.info("Cleared rates history")


# Глобальный экземпляр хранилища
storage = RatesStorage()