import json
import os
import shlex

from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError, InsufficientFundsError
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def parse_args(args_line: str) -> dict:
    parts = shlex.split(args_line) if args_line else []
    kwargs = {}
    i = 0
    while i < len(parts):
        if parts[i].startswith('--'):
            key = parts[i][2:]
            if i + 1 < len(parts) and not parts[i+1].startswith('--'):
                kwargs[key] = parts[i+1]
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            i += 1
    return kwargs


def show_help():
    print("""
Доступные команды:
  register --username <имя> --password <пароль>        - регистрация нового пользователя
  login    --username <имя> --password <пароль>        - вход в систему
  show-portfolio [--base <валюта>]                      - показать портфель (база по умолчанию USD)
  buy      --currency <код> --amount <количество>      - купить валюту (за USD)
  sell     --currency <код> --amount <количество>      - продать валюту (за USD)
  get-rate --from <валюта> --to <валюта>                - получить курс
  update-rates                                          - принудительно обновить курсы из внешних API
  show-rates [--currency <код>] [--top N] [--base <валюта>] - показать кэшированные курсы
  exit                                                   - выход
  help                                                   - эта справка
""")


def main_loop():
    print("Добро пожаловать в платформу торговли валютами!")
    show_help()
    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue
            if line == "exit":
                print("До свидания!")
                break
            if line == "help":
                show_help()
                continue

            parts = line.split(maxsplit=1)
            cmd = parts[0]
            args_line = parts[1] if len(parts) > 1 else ""
            kwargs = parse_args(args_line)

            match cmd:
                case "register":
                    username = kwargs.get("username")
                    password = kwargs.get("password")
                    if not username or not password:
                        print("Использование: register --username <имя> --password <пароль>")
                        continue
                    try:
                        result = usecases.register(username, password)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка: {e}")

                case "update-rates":
                    # Можно добавить опциональный параметр --source, но пока не усложняем
                    try:
                        settings = SettingsLoader()
                        config = ParserConfig()  # используем переменные окружения
                        # Переопределим пути из настроек, если нужно
                        config.RATES_FILE_PATH = settings.get('data_path', 'data/') + "rates.json"
                        config.HISTORY_FILE_PATH = settings.get('data_path', 'data/') + "exchange_rates.json"

                        storage = RatesStorage(config.HISTORY_FILE_PATH, config.RATES_FILE_PATH)
                        updater = RatesUpdater(config, storage)
                        result = updater.run_update()

                        if result["errors"]:
                            print("Update completed with errors:")
                            for err in result["errors"]:
                                print(f"  - {err}")
                        else:
                            print(
                                f"Update successful. Total rates updated: {result['total']}."
                                f"Last refresh: {result['last_refresh']}"
                                )
                    except Exception as e:
                        print(f"Update failed: {str(e)}")

                case "show-rates":
                    currency = kwargs.get("currency")
                    top = kwargs.get("top")
                    base = kwargs.get("base", "USD")
                    try:
                        settings = SettingsLoader()
                        rates_path = settings.get('data_path', 'data/') + "rates.json"
                        if not os.path.exists(rates_path):
                            print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
                            continue

                        with open(rates_path, 'r', encoding='utf-8') as f:
                            cache = json.load(f)

                        pairs = cache.get("pairs", {})
                        last_refresh = cache.get("last_refresh", "unknown")

                        if not pairs:
                            print("В кеше нет данных.")
                            continue

                        # Фильтрация по валюте (если указана)
                        if currency:
                            filtered = {k: v for k, v in pairs.items() if k.startswith(currency.upper() + '_')}
                            if not filtered:
                                print(f"Курс для '{currency}' не найден в кеше.")
                                continue
                            pairs = filtered

                        # Преобразуем в список для сортировки
                        items = list(pairs.items())
                        if top:
                            try:
                                top_n = int(top)
                                items.sort(key=lambda x: x[1]['rate'], reverse=True)
                                items = items[:top_n]
                            except ValueError:
                                pass

                        # Создаём таблицу PrettyTable
                        table = PrettyTable()
                        table.field_names = ["Pair", "Rate"]
                        for pair, data in items:
                            # Округление до 5 знаков для красоты
                            table.add_row([pair, f"{data['rate']:.5f}"])

                        print(f"Rates from cache (updated at {last_refresh}):")
                        print(table)

                    except Exception as e:
                        print(f"Ошибка при показе курсов: {e}")

                case "login":
                    username = kwargs.get("username")
                    password = kwargs.get("password")
                    if not username or not password:
                        print("Использование: login --username <имя> --password <пароль>")
                        continue
                    try:
                        result = usecases.login(username, password)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка: {e}")

                case "show-portfolio":
                    base = kwargs.get("base", "USD")
                    try:
                        result = usecases.show_portfolio(base)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка: {e}")
                    except CurrencyNotFoundError as e:
                        print(f"Ошибка: {e}\nПроверьте поддерживаемые коды валют (например, USD, EUR, BTC, ETH).")

                case "buy":
                    currency = kwargs.get("currency")
                    amount_str = kwargs.get("amount")
                    if not currency or not amount_str:
                        print("Использование: buy --currency <код> --amount <количество>")
                        continue
                    try:
                        amount = float(amount_str)
                        result = usecases.buy(currency, amount)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка ввода: {e}")
                    except InsufficientFundsError as e:
                        print(e)  # выводим сообщение как есть
                    except CurrencyNotFoundError as e:
                        print(f"Ошибка: {e}\nПроверьте поддерживаемые коды валют (например, USD, EUR, BTC, ETH).")
                    except ApiRequestError as e:
                        print(f"Ошибка API: {e}. Повторите попытку позже.")

                case "sell":
                    currency = kwargs.get("currency")
                    amount_str = kwargs.get("amount")
                    if not currency or not amount_str:
                        print("Использование: sell --currency <код> --amount <количество>")
                        continue
                    try:
                        amount = float(amount_str)
                        result = usecases.sell(currency, amount)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка: {e}")
                    except InsufficientFundsError as e:
                        print(e)
                    except CurrencyNotFoundError as e:
                        print(f"Ошибка: {e}\nПроверьте поддерживаемые коды валют (например, USD, EUR, BTC, ETH).")
                    except ApiRequestError as e:
                        print(f"Ошибка API: {e}. Повторите попытку позже.")

                case "get-rate":
                    from_curr = kwargs.get("from")
                    to_curr = kwargs.get("to")
                    if not from_curr or not to_curr:
                        print("Использование: get-rate --from <валюта> --to <валюта>")
                        continue
                    try:
                        result = usecases.get_rate(from_curr, to_curr)
                        print(result)
                    except ValueError as e:
                        print(f"Ошибка: {e}")
                    except CurrencyNotFoundError as e:
                        print(f"Ошибка: {e}\nПроверьте поддерживаемые коды валют (например, USD, EUR, BTC, ETH).")
                    except ApiRequestError as e:
                        print(f"Ошибка API: {e}. Повторите попытку позже.")

                case "logout":
                    usecases.logout()
                    print("Вы вышли из системы.")

                case _:
                    print("Неизвестная команда. Введите 'help' для справки.")
        except KeyboardInterrupt:
            print("\nВыход.")
            break
