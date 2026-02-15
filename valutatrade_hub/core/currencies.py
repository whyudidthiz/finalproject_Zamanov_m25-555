# valutatrade_hub/core/currencies.py

from abc import ABC, abstractmethod
from typing import Dict, Optional
from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для всех валют."""

    def __init__(self, code: str, name: str):
        self.code = self._validate_code(code)
        self.name = self._validate_name(name)

    @staticmethod
    def _validate_code(code: str) -> str:
        if not code or not isinstance(code, str):
            raise ValueError("Код валюты должен быть непустой строкой.")
        code = code.upper().strip()
        if not (2 <= len(code) <= 5) or not code.isalnum():
            raise ValueError("Код валюты должен содержать 2-5 букв/цифр, без пробелов.")
        return code

    @staticmethod
    def _validate_name(name: str) -> str:
        if not name or not name.strip():
            raise ValueError("Название валюты не может быть пустым.")
        return name.strip()

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для вывода пользователю."""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта (доллар, евро и т.д.)."""

    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта (биткоин, эфир и т.д.)."""

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float):
        super().__init__(code, name)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        # Форматируем капитализацию в научной нотации для компактности
        cap_str = f"{self.market_cap:.2e}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {cap_str})"


# --- Реестр валют (фабрика) ---
_currency_registry: Dict[str, Currency] = {
    "USD": FiatCurrency("USD", "US Dollar", "United States"),
    "EUR": FiatCurrency("EUR", "Euro", "Eurozone"),
    "RUB": FiatCurrency("RUB", "Russian Ruble", "Russia"),
    "BTC": CryptoCurrency("BTC", "Bitcoin", "SHA-256", 1_200_000_000_000),
    "ETH": CryptoCurrency("ETH", "Ethereum", "Ethash", 500_000_000_000),
}


def get_currency(code: str) -> Currency:
    """
    Возвращает объект валюты по её коду.
    Если код отсутствует в реестре, выбрасывает CurrencyNotFoundError.
    """
    code = code.upper().strip()
    if code not in _currency_registry:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не найдена.")
    return _currency_registry[code]


def register_currency(currency: Currency) -> None:
    """Позволяет добавить новую валюту в реестр (для расширяемости)."""
    _currency_registry[currency.code] = currency