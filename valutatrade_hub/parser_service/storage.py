import json
import os
from datetime import datetime
from typing import Dict, List
import tempfile

from .config import ParserConfig


class RatesStorage:
    """Хранилище для курсов валют"""

    def __init__(self, config: ParserConfig):
        self.config = config
        self._ensure_directories()

    def _ensure_directories(self):
        """Создает необходимые директории"""
        os.makedirs(os.path.dirname(self.config.RATES_FILE_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(self.config.HISTORY_FILE_PATH), exist_ok=True)

    def save_current_rates(self, rates: Dict[str, float], source: str = "ParserService"):
        """Сохранить текущие курсы в rates.json"""
        timestamp = datetime.now().isoformat()

        # Формируем данные для сохранения
        rates_data = {
            "pairs": {},
            "last_refresh": timestamp,
            "source": source
        }

        for pair, rate in rates.items():
            rates_data["pairs"][pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source
            }

        # Атомарная запись (через временный файл)
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                    mode='w',
                    dir=os.path.dirname(self.config.RATES_FILE_PATH),
                    delete=False,
                    encoding='utf-8'
            ) as f:
                json.dump(rates_data, f, indent=2, ensure_ascii=False)
                temp_file = f.name

            # Перемещаем временный файл в целевой
            os.replace(temp_file, self.config.RATES_FILE_PATH)

        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            raise

    def save_to_history(self, rates: Dict[str, float], source: str, meta: Dict = None):
        """Сохранить курсы в историю (exchange_rates.json)"""
        timestamp = datetime.now().isoformat()

        try:
            # Загружаем существующую историю
            if os.path.exists(self.config.HISTORY_FILE_PATH):
                with open(self.config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []

            # Добавляем новые записи
            for pair, rate in rates.items():
                history_entry = {
                    "id": f"{pair}_{timestamp.replace(':', '-').replace('.', '-')}",
                    "from_currency": pair.split('_')[0],
                    "to_currency": pair.split('_')[1],
                    "rate": rate,
                    "timestamp": timestamp,
                    "source": source,
                    "meta": meta or {}
                }
                history.append(history_entry)

            # Сохраняем историю
            with open(self.config.HISTORY_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Ошибка при сохранении истории: {e}")