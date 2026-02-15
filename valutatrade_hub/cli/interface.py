import shlex
from valutatrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError, ApiRequestError
from valutatrade_hub.core import usecases


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

                case _:
                    print("Неизвестная команда. Введите 'help' для справки.")
        except KeyboardInterrupt:
            print("\nВыход.")
            break