import json
import os
from typing import Dict, List


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)

        # Инициализируем файлы если их нет
        self._init_files()

    def _init_files(self):
        default_files = {
            "users.json": [],
            "portfolios.json": [],
            "rates.json": {
                "pairs": {
                    "EUR_USD": {"rate": 1.0786, "updated_at": "2025-10-09T10:30:00", "source": "ParserService"},
                    "BTC_USD": {"rate": 59337.21, "updated_at": "2025-10-09T10:29:42", "source": "ParserService"},
                    "RUB_USD": {"rate": 0.01016, "updated_at": "2025-10-09T10:31:12", "source": "ParserService"},
                    "ETH_USD": {"rate": 3720.00, "updated_at": "2025-10-09T10:35:00", "source": "ParserService"},
                },
                "last_refresh": "2025-10-09T10:35:00",
                "source": "ParserService"
            },
            "exchange_rates.json": []
        }

        for filename, default_data in default_files.items():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=2, ensure_ascii=False)

    def load_users(self) -> List[Dict]:
        filepath = os.path.join(self.data_dir, "users.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_users(self, users: List[Dict]):
        filepath = os.path.join(self.data_dir, "users.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)

    def load_portfolios(self) -> List[Dict]:
        filepath = os.path.join(self.data_dir, "portfolios.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_portfolios(self, portfolios: List[Dict]):
        filepath = os.path.join(self.data_dir, "portfolios.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(portfolios, f, indent=2, ensure_ascii=False)

    def load_rates(self) -> Dict:
        filepath = os.path.join(self.data_dir, "rates.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_rates(self, rates: Dict):
        filepath = os.path.join(self.data_dir, "rates.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rates, f, indent=2, ensure_ascii=False)

    def load_exchange_rates(self) -> List[Dict]:
        filepath = os.path.join(self.data_dir, "exchange_rates.json")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_exchange_rates(self, exchange_rates: List[Dict]):
        filepath = os.path.join(self.data_dir, "exchange_rates.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(exchange_rates, f, indent=2, ensure_ascii=False)