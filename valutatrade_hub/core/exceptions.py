# valutatrade_hub/core/exceptions.py

class CurrencyNotFoundError(Exception):
    """Исключение, возникающее при запросе неизвестного кода валюты."""
    pass

class InsufficientFundsError(Exception):
    """Исключение при недостатке средств на кошельке."""

    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(f"Недостаточно средств: доступно {available:.2f} {code}, требуется {required:.2f} {code}")


class ApiRequestError(Exception):
    """Исключение при сбое внешнего API."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")
