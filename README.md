ValutaTrade Hub - это комплексная платформа для симуляции торговли валютами, состоящая из двух основных сервисов:

1. Core Service - основное приложение с CLI интерфейсом для управления пользователями, портфелями и транзакциями
2. Parser Service - микросервис для сбора актуальных курсов валют из внешних API (CoinGecko и ExchangeRate-API)

Доступные команды

1. Регистрация нового пользователя

```
poetry run project register --username <имя> --password <пароль>
```

Пример:

```
> register --username alice --password 1234
Пользователь 'alice' зарегистрирован (id=1). Войдите: login --username alice --password 1234
```

2. Вход в систему

```
poetry run project login --username <имя> --password <пароль>
```

Пример:

```
> login --username alice --password 1234
Вы вошли как 'alice'
```

3. Просмотр портфеля

```
poetry run project show-portfolio [--base <валюта>]
```

Пример:

```
> show-portfolio
Портфель пользователя 'alice' (база: USD):
- USD: 150.00 → 150.00 USD
- BTC: 0.0500 → 2965.00 USD
- EUR: 200.00 → 214.00 USD

ИТОГО: 3,329.00 USD
```

4. Покупка валюты

```
poetry run project buy --currency <код> --amount <количество>
```

Пример:

```
> buy --currency BTC --amount 0.05
Покупка выполнена: 0.0500 BTC по курсу $59300.00 USD/BTC

Изменения в портфеле:
- BTC: было 0.0000 → стало 0.0500
Оценочная стоимость покупки: 2,965.00 USD
```

5. Продажа валюты

```
poetry run project sell --currency <код> --amount <количество>
```

Пример:

```
> sell --currency BTC --amount 0.01
Продажа выполнена: 0.0100 BTC по курсу 59900.00 USD/BTC

Изменения в портфеле:
- BTC: было 0.0500 → стало 0.0400
Оценочная выручка: 599.00 USD
```

6. Получение курса валюты

```
poetry run project get-rate --from <валюта> --to <валюта>
```

Пример:

```
> get-rate --from USD --to BTC
Курс USD=BTC: 0.00001685 (обновлено: 2025-10-09 00:03:22)
Обратный курс BTC=USD: 59337.21
```

7. Обновление курсов

```
poetry run project update-rates [--source <источник>]
```

Пример:

```
> update-rates
INFO: Starting rates update...
INFO: Fetching from CoinGecko... OK (3 rates)
INFO: Fetching from ExchangeRate-API... OK (3 rates)
INFO: Writing 6 rates to data/rates.json...
Update successful. Total rates updated: 6. Last refresh: 2025-10-10T15:30:00
```

8. Просмотр всех курсов

```
poetry run project show-rates --currency <код> --base <валюта>
```

Пример:

```
> show-rates
Rates from cache (updated at 2025-10-10T15:30:00):
  - BTC_USD: 59337.21
  - ETH_USD: 3720.00
```

На все команды реализован интерактивный Makefile, для вызова списка доступных команд: "make project"
Создан файл test_session для быстрого тестирования проекта. Вызов через команду "make test"

Демонстрация работоспособности: https://asciinema.org/a/uhHcvyYyDSJw5aLxYq4g5YmOT
