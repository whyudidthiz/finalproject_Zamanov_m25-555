import hashlib
from typing import Optional, List, Dict
from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.core import utils

# Глобальное состояние
_current_user: Optional[User] = None
_users: List[User] = []
_portfolios: Dict[int, Portfolio] = {}


def _load_all():
    global _users, _portfolios
    users_data = utils.load_users()
    portfolios_data = utils.load_portfolios()

    _users = [User.from_dict(u) for u in users_data]
    users_by_id = {u.user_id: u for u in _users}

    _portfolios = {}
    for pd in portfolios_data:
        uid = pd['user_id']
        if uid in users_by_id:
            _portfolios[uid] = Portfolio.from_dict(pd, users_by_id[uid])


def _save_all():
    utils.save_users([u.to_dict() for u in _users])
    utils.save_portfolios([p.to_dict() for p in _portfolios.values()])


# Загружаем данные при старте
_load_all()


def register(username: str, password: str) -> str:
    if any(u.username == username for u in _users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")
    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов")

    new_id = max((u.user_id for u in _users), default=0) + 1
    user = User(new_id, username, password)
    _users.append(user)

    # Создаём портфель с начальным USD кошельком (1000 для демонстрации)
    portfolio = Portfolio(user)
    portfolio._wallets["USD"] = Wallet("USD", 1000.0)
    _portfolios[user.user_id] = portfolio

    _save_all()
    return f"Пользователь '{username}' зарегистрирован (id={new_id}). Войдите: login --username {username} --password ****"


def login(username: str, password: str) -> str:
    global _current_user
    user = next((u for u in _users if u.username == username), None)
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")
    _current_user = user
    return f"Вы вошли как '{username}'"


def logout():
    global _current_user
    _current_user = None


def get_current_user() -> Optional[User]:
    return _current_user


def show_portfolio(base_currency: str = "USD") -> str:
    if not _current_user:
        raise ValueError("Сначала выполните login")
    portfolio = _portfolios.get(_current_user.user_id)
    if not portfolio:
        raise ValueError("Портфель не найден")

    rates = utils.load_rates()
    lines = [f"Портфель пользователя '{_current_user.username}' (база: {base_currency}):"]
    total = 0.0
    if not portfolio.wallets:
        lines.append("  Кошельков нет.")
    else:
        for code, wallet in portfolio.wallets.items():
            balance = wallet.balance
            # Конвертация
            rate_key = f"{code}_{base_currency}"
            inv_key = f"{base_currency}_{code}"
            rate = None
            if rate_key in rates:
                rate = rates[rate_key]['rate']
            elif inv_key in rates:
                rate = 1.0 / rates[inv_key]['rate']
            if rate is None:
                converted = 0.0
                rate_str = "N/A"
            else:
                converted = balance * rate
                total += converted
                rate_str = f"{rate:.4f}"
            lines.append(f"  - {code}: {balance:.2f}  → {converted:.2f} {base_currency} (курс: {rate_str})")
    lines.append("-" * 40)
    lines.append(f"ИТОГО: {total:.2f} {base_currency}")
    return "\n".join(lines)


def buy(currency: str, amount: float) -> str:
    if not _current_user:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    currency = currency.upper()
    portfolio = _portfolios[_current_user.user_id]

    # Курс к USD
    rates = utils.load_rates()
    rate_key = f"{currency}_USD"
    inv_key = f"USD_{currency}"
    rate = None
    if rate_key in rates:
        rate = rates[rate_key]['rate']
    elif inv_key in rates:
        rate = 1.0 / rates[inv_key]['rate']
    else:
        raise ValueError(f"Не удалось получить курс для {currency}→USD")
    cost = amount * rate

    usd_wallet = portfolio.get_wallet("USD")
    if usd_wallet.balance < cost:
        raise ValueError(f"Недостаточно USD: доступно {usd_wallet.balance:.2f}, требуется {cost:.2f}")

    usd_wallet.withdraw(cost)
    if currency in portfolio.wallets:
        target = portfolio.get_wallet(currency)
    else:
        portfolio.add_currency(currency)
        target = portfolio.get_wallet(currency)
    target.deposit(amount)

    _save_all()
    return (f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"- {currency}: было {target.balance - amount:.4f} → стало {target.balance:.4f}\n"
            f"- USD: было {usd_wallet.balance + cost:.2f} → стало {usd_wallet.balance:.2f}\n"
            f"Оценочная стоимость покупки: {cost:.2f} USD")


def sell(currency: str, amount: float) -> str:
    if not _current_user:
        raise ValueError("Сначала выполните login")
    if amount <= 0:
        raise ValueError("amount должен быть положительным числом")
    currency = currency.upper()
    portfolio = _portfolios[_current_user.user_id]

    if currency not in portfolio.wallets:
        raise ValueError(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")
    target = portfolio.get_wallet(currency)
    if target.balance < amount:
        raise ValueError(f"Недостаточно средств: доступно {target.balance:.4f} {currency}, требуется {amount:.4f}")

    rates = utils.load_rates()
    rate_key = f"{currency}_USD"
    inv_key = f"USD_{currency}"
    rate = None
    if rate_key in rates:
        rate = rates[rate_key]['rate']
    elif inv_key in rates:
        rate = 1.0 / rates[inv_key]['rate']
    else:
        raise ValueError(f"Не удалось получить курс для {currency}→USD")
    proceeds = amount * rate

    target.withdraw(amount)
    usd_wallet = portfolio.get_wallet("USD")
    usd_wallet.deposit(proceeds)

    _save_all()
    return (f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"- {currency}: было {target.balance + amount:.4f} → стало {target.balance:.4f}\n"
            f"- USD: было {usd_wallet.balance - proceeds:.2f} → стало {usd_wallet.balance:.2f}\n"
            f"Оценочная выручка: {proceeds:.2f} USD")


def get_rate(from_curr: str, to_curr: str) -> str:
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()
    rates = utils.load_rates()
    direct_key = f"{from_curr}_{to_curr}"
    if direct_key in rates:
        data = rates[direct_key]
        rate = data['rate']
        updated = data['updated_at']
    else:
        inv_key = f"{to_curr}_{from_curr}"
        if inv_key in rates:
            inv_data = rates[inv_key]
            inv_rate = inv_data['rate']
            rate = 1.0 / inv_rate if inv_rate != 0 else 0
            updated = inv_data['updated_at']
        else:
            raise ValueError(f"Курс {from_curr}→{to_curr} недоступен")
    return (f"Курс {from_curr}→{to_curr}: {rate:.8f} (обновлено: {updated})\n"
            f"Обратный курс {to_curr}→{from_curr}: {1.0/rate:.8f}" if rate != 0 else "Курс равен нулю")