import json
import os
import shutil
from datetime import datetime
from typing import Dict


class RatesStorage:
    """Управляет сохранением курсов в exchange_rates.json и rates.json."""

    def __init__(self, history_path: str, cache_path: str):
        self.history_path = history_path
        self.cache_path = cache_path
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)

    def save_historical_rates(self, rates_dict: Dict[str, float], source: str) -> None:
        """
        Сохраняет каждый курс как отдельную запись в исторический файл.
        rates_dict: {'BTC_USD': 59337.21, 'EUR_USD': 1.0786}
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'  # UTC в формате ISO
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

        for pair, rate in rates_dict.items():
            from_curr, to_curr = pair.split('_')
            record_id = f"{from_curr}_{to_curr}_{timestamp}"
            record = {
                "id": record_id,
                "from_currency": from_curr,
                "to_currency": to_curr,
                "rate": rate,
                "timestamp": timestamp,
                "source": source,
                "meta": {}
            }
            history.append(record)

        temp_path = self.history_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        shutil.move(temp_path, self.history_path)

    def update_cache(self, rates_dict: Dict[str, float], source_map: Dict[str, str]) -> None:
        """
        Обновляет rates.json (кэш последних значений).
        source_map: {'BTC_USD': 'CoinGecko', 'EUR_USD': 'ExchangeRate-API'}
        """
        cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                cache = json.load(f)

        if "pairs" not in cache:
            cache["pairs"] = {}

        timestamp = datetime.utcnow().isoformat() + 'Z'
        for pair, rate in rates_dict.items():
            cache["pairs"][pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": source_map.get(pair, "unknown")
            }

        cache["last_refresh"] = timestamp

        temp_path = self.cache_path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        shutil.move(temp_path, self.cache_path)
