import json
import os
from datetime import datetime
from typing import Any


def get_data_path(filename: str) -> str:
    """Возвращает полный путь к файлу в папке data."""
    base = os.path.join(os.getcwd(), 'data')
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def load_json(filename: str, default: Any) -> Any:
    path = get_data_path(filename)
    if not os.path.exists(path):
        return default
    if os.path.getsize(path) == 0:   # если файл пуст
        return default
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    path = get_data_path(filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_users() -> list:
    return load_json('users.json', [])


def save_users(users: list) -> None:
    save_json('users.json', users)


def load_portfolios() -> list:
    return load_json('portfolios.json', [])


def save_portfolios(portfolios: list) -> None:
    save_json('portfolios.json', portfolios)


def load_rates() -> dict:
    default = {
        "EUR_USD": {"rate": 1.08, "updated_at": datetime.now().isoformat()},
        "BTC_USD": {"rate": 50000.0, "updated_at": datetime.now().isoformat()},
        "RUB_USD": {"rate": 0.012, "updated_at": datetime.now().isoformat()},
        "ETH_USD": {"rate": 3000.0, "updated_at": datetime.now().isoformat()},
        "source": "Local fallback",
        "last_refresh": datetime.now().isoformat()
    }
    return load_json('rates.json', default)


def save_rates(rates: dict) -> None:
    save_json('rates.json', rates)