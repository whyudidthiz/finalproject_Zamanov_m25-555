# Платформа для отслеживания и симуляции торговли валютами

## Установка и настройка

### Требования
- Python 3.13+
- Poetry (рекомендуется) или pip
- Доступ к интернету для загрузки зависимостей и получения курсов

### Шаги

1. **Клонируйте репозиторий:**
    ```bash
      git clone https://github.com/whyudidthiz/finalproject_Zamanov_m25-555.git
      cd finalproject_Zamanov_m25-555
2. **Установите зависимости через Poetry:**
    ```bash
      poetry install
3. В корне проекта найдите .env и вставьте сюда API ключ, полученный при бесплатной регистрации на сайте
   ```bash
     https://www.exchangerate-api.com/
4. **Активируйте виртуальное окружение и запустите игру**
    ```bash
      make install
      make package-install
      make build
      make project

### Пример работы программы 

> update-rates
2026-02-16T05:35:42.178 INFO Starting rates update...
2026-02-16T05:35:42.668 INFO CoinGeckoClient: OK (3 rates)
2026-02-16T05:35:43.229 INFO ExchangeRateApiClient: OK (3 rates)
2026-02-16T05:35:43.236 INFO Cache updated with 6 rates
Update successful. Total rates updated: 6. Last refresh: 2026-02-16T00:35:43.237027Z

> register --username ivan --password 1234
2026-02-16T05:37:35.117 INFO action=REGISTER user=anonymous base=USD result=OK
Пользователь 'ivan' зарегистрирован (id=4). Войдите: login --username ivan --password ****

> login --username ivan --password 1234
2026-02-16T05:39:17.367 INFO action=LOGIN user=anonymous base=USD result=OK
Вы вошли как 'ivan'

> show-portfolio
Портфель пользователя 'ivan' (база: USD):
  - USD: 1000.00  → 1000.00 USD (курс: 1.0000)
----------------------------------------
ИТОГО: 1000.00 USD

> get-rate --from BTC --to USD
Курс BTC→USD: 68875.00000000 (обновлено: 2026-02-16T00:35:43.234889Z)
Обратный курс USD→BTC: 0.00001452

> buy --currency BTC --amount 0.05
Недостаточно средств: доступно 1000.00 USD, требуется 3443.75 USD

> buy --currency BTC --amount 0.001
2026-02-16T05:41:21.695 INFO action=BUY user=ivan user_id=4 base=USD result=OK
Покупка выполнена: 0.0010 BTC по курсу 68875.00 USD/BTC
Изменения в портфеле:
- BTC: было 0.0000 → стало 0.0010
- USD: было 1000.00 → стало 931.12
Оценочная стоимость покупки: 68.88 USD

> show-portfolio
Портфель пользователя 'ivan' (база: USD):
  - USD: 931.12  → 931.12 USD (курс: 1.0000)
  - BTC: 0.0010 → 68.88 USD (курс: 68875.0000)
----------------------------------------
ИТОГО: 1000.00 USD

> show-rates --top 2
Rates from cache (updated at 2026-02-16T00:35:43.234889Z):
+---------+-------------+
|   Pair  |     Rate    |
+---------+-------------+
| BTC_USD | 68875.00000 |
| ETH_USD |  1970.84000 |
+---------+-------------+

> show-rates --currency RUB
Rates from cache (updated at 2026-02-16T00:35:43.234889Z):
+---------+----------+
|   Pair  |   Rate   |
+---------+----------+
| RUB_USD | 77.14960 |
+---------+----------+

> show-rates
Rates from cache (updated at 2026-02-16T00:35:43.234889Z):
+---------+-------------+
|   Pair  |     Rate    |
+---------+-------------+
| BTC_USD | 68875.00000 |
| ETH_USD |  1970.84000 |
| SOL_USD |   85.93000  |
| EUR_USD |   0.84280   |
| GBP_USD |   0.73320   |
| RUB_USD |   77.14960  |
+---------+-------------+

> update-rates
2026-02-16T05:43:05.120 INFO Starting rates update...
2026-02-16T05:43:05.660 INFO CoinGeckoClient: OK (3 rates)
2026-02-16T05:43:06.224 INFO ExchangeRateApiClient: OK (3 rates)
2026-02-16T05:43:06.236 INFO Cache updated with 6 rates
Update successful. Total rates updated: 6. Last refresh: 2026-02-16T00:43:06.236941Z

> show-rates
Rates from cache (updated at 2026-02-16T00:43:06.233380Z):
+---------+-------------+
|   Pair  |     Rate    |
+---------+-------------+
| BTC_USD | 68812.00000 |
| ETH_USD |  1966.12000 |
| SOL_USD |   86.08000  |
| EUR_USD |   0.84280   |
| GBP_USD |   0.73320   |
| RUB_USD |   77.14960  |
+---------+-------------+
