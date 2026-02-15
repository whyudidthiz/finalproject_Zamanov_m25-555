import json
import os
from typing import Any, Optional


class SettingsLoader:
    """Singleton для загрузки и доступа к конфигурации проекта."""

    _instance = None
    _config = None

    def __new__(cls, config_path: str = "config.json"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_path = config_path
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Загружает конфигурацию из JSON-файла."""
        if not os.path.exists(self._config_path):
            # Если файла нет, создаём конфигурацию по умолчанию
            self._config = self._default_config()
            self._save_config()
        else:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)

    def _save_config(self) -> None:
        """Сохраняет текущую конфигурацию в файл."""
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _default_config() -> dict:
        return {
            "data_path": "data/",
            "rates_ttl_seconds": 300,
            "default_base_currency": "USD",
            "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "log_file": "logs/trade.log"
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение параметра конфигурации."""
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла."""
        self._load_config()