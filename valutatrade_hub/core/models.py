import hashlib
import datetime
import os
from typing import Dict, Optional, Any


class User:
    """Класс пользователя системы."""

    def __init__(self, user_id: int, username: str, password: str):
        self._user_id = user_id
        self._username = self._validate_username(username)
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = datetime.datetime.now()

    @staticmethod
    def _generate_salt() -> str:
        return os.urandom(16).hex()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    @staticmethod
    def _validate_username(username: str) -> str:
        if not username or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        return username.strip()

    @staticmethod
    def _validate_password(password: str) -> str:
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        return password

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        self._username = self._validate_username(value)

    @property
    def registration_date(self) -> datetime.datetime:
        return self._registration_date

    def get_user_info(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "registration_date": self.registration_date.isoformat()
        }

    def change_password(self, new_password: str) -> None:
        self._validate_password(new_password)
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        return self._hashed_password == self._hash_password(password, self._salt)

    @classmethod
    def from_dict(cls, data: dict):
        """Создаёт объект User из словаря (для загрузки из JSON)."""
        user = cls.__new__(cls)
        user._user_id = data['user_id']
        user._username = data['username']
        user._hashed_password = data['hashed_password']
        user._salt = data['salt']
        user._registration_date = datetime.datetime.fromisoformat(data['registration_date'])
        return user

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self.registration_date.isoformat()
        }


class Wallet:
    """Кошелёк для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным числом.")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом.")
        if amount > self._balance:
            raise ValueError("Недостаточно средств.")
        self._balance -= amount

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self._balance:.2f}"


class Portfolio:
    """Управляет кошельками одного пользователя."""

    EXCHANGE_RATES = {
        "USD": 1.0,
        "EUR": 1.1,
        "RUB": 0.012,
        "BTC": 50000.0,
        "ETH": 3000.0
    }

    def __init__(self, user: User):
        self._user = user
        self._wallets: Dict[str, Wallet] = {}

    @property
    def user(self) -> User:
        return self._user

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> None:
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк для валюты {code} уже существует.")
        self._wallets[code] = Wallet(code)

    def get_wallet(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code not in self._wallets:
            raise KeyError(f"Кошелёк для валюты {code} не найден.")
        return self._wallets[code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        if base_currency.upper() not in self.EXCHANGE_RATES:
            raise ValueError(f"Курс для базовой валюты {base_currency} не задан.")
        total = 0.0
        base_rate = self.EXCHANGE_RATES[base_currency.upper()]
        for code, wallet in self._wallets.items():
            if code not in self.EXCHANGE_RATES:
                continue
            rate = self.EXCHANGE_RATES[code] / base_rate
            total += wallet.balance * rate
        return total

    def to_dict(self) -> dict:
        return {
            "user_id": self.user.user_id,
            "wallets": {code: {"balance": w.balance} for code, w in self._wallets.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, user: User):
        portfolio = cls(user)
        for code, wdata in data['wallets'].items():
            wallet = Wallet(code, wdata['balance'])
            portfolio._wallets[code] = wallet
        return portfolio