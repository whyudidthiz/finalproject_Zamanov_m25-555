from abc import ABC, abstractmethod
from typing import Any, Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import ParserConfig


class BaseApiClient(ABC):
    """Абстрактный базовый класс для клиентов API курсов валют."""

    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Возвращает словарь вида {'BTC_USD': 59337.21, ...}
        В случае ошибки выбрасывает ApiRequestError.
        """
        pass

    def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """Общий метод для выполнения HTTP-запроса."""
        try:
            response = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise ApiRequestError(f"Timeout при запросе к {url}")
        except requests.exceptions.ConnectionError:
            raise ApiRequestError(f"Ошибка соединения с {url}")
        except requests.exceptions.HTTPError as e:
            # Попробуем извлечь детали из ответа
            try:
                error_data = response.json()
                error_msg = error_data.get('error', str(e))
            except Exception:
                error_msg = str(e)
            raise ApiRequestError(f"HTTP ошибка {response.status_code}: {error_msg}")
        except Exception as e:
            raise ApiRequestError(f"Неизвестная ошибка: {str(e)}")


class CoinGeckoClient(BaseApiClient):
    """Клиент для получения криптовалютных курсов."""

    def fetch_rates(self) -> Dict[str, float]:
        # Формируем список ID для запроса
        crypto_ids = [self.config.CRYPTO_ID_MAP[code]
                      for code in self.config.CRYPTO_CURRENCIES
                      if code in self.config.CRYPTO_ID_MAP]
        if not crypto_ids:
            return {}

        params = {
            'ids': ','.join(crypto_ids),
            'vs_currencies': self.config.BASE_CURRENCY.lower()
        }

        data = self._make_request(self.config.COINGECKO_URL, params)

        # Преобразуем ответ в стандартный формат
        result = {}
        for code, coin_id in self.config.CRYPTO_ID_MAP.items():
            if coin_id in data and self.config.BASE_CURRENCY.lower() in data[coin_id]:
                rate = data[coin_id][self.config.BASE_CURRENCY.lower()]
                pair = f"{code}_{self.config.BASE_CURRENCY}"
                result[pair] = rate
        return result


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для получения фиатных курсов."""

    def fetch_rates(self) -> Dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("API ключ для ExchangeRate-API не задан")

        # Формируем URL: https://v6.exchangerate-api.com/v6/KEY/latest/USD
        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
                f"{self.config.EXCHANGERATE_API_KEY}/latest/"
                f"{self.config.BASE_CURRENCY}"
                )
        data = self._make_request(url)

        if data.get('result') != 'success':
            error_msg = data.get('error-type', 'Unknown error')
            raise ApiRequestError(f"ExchangeRate-API вернул ошибку: {error_msg}")

        rates = data.get('conversion_rates', {})
        result = {}
        for code in self.config.FIAT_CURRENCIES:
            if code in rates:
                pair = f"{code}_{self.config.BASE_CURRENCY}"
                result[pair] = rates[code]
        return result
