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
            status_code = e.response.status_code if e.response else 0
            # Пытаемся получить детали из ответа (если есть JSON)
            try:
                error_data = e.response.json() if e.response else {}
                api_error = error_data.get('error', error_data.get('message', ''))
            except Exception:
                api_error = ''
            if api_error:
                error_msg = api_error
            elif status_code == 401:
                error_msg = "Неверный API ключ или доступ запрещён (401)"
            elif status_code == 403:
                error_msg = "Доступ запрещён (403)"
            elif status_code == 404:
                error_msg = "Ресурс не найден (404)"
            elif status_code == 429:
                error_msg = "Слишком много запросов (429). Попробуйте позже."
            elif 500 <= status_code < 600:
                error_msg = f"Ошибка сервера ({status_code})"
            else:
                error_msg = f"HTTP {status_code}"
            raise ApiRequestError(f"Ошибка при обращении к внешнему API: {error_msg}")
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
