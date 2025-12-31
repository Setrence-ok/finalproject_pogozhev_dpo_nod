import argparse
import sys
from datetime import datetime

from ..core.usecases import UserUseCases, PortfolioUseCases, RatesUseCases
from ..core.utils import SessionManager
from ..core.exceptions import InsufficientFundsError, CurrencyNotFoundError
from ..parser_service.updater import RatesUpdater
from ..parser_service.config import ParserConfig
from ..logging_config import setup_logging


def handle_update_rates(source: str = None) -> int:
    """Обработка команды update-rates с реальными API запросами"""
    print("INFO: Starting rates update...")

    try:
         # Настраиваем логирование
        setup_logging()

        # Создаем конфигурацию с вашим API ключом
        config = ParserConfig()

        # Проверяем API ключ
        if not config.EXCHANGERATE_API_KEY or config.EXCHANGERATE_API_KEY == "c7ef33caebf0f8f2f5ee6bd3":
            print(f"Используется API ключ: {config.EXCHANGERATE_API_KEY[:10]}...")
        else:
            print("Используется предоставленный API ключ")

        # Создаем и запускаем updater
        updater = RatesUpdater(config)

        if source:
            print(f"INFO: Updating only from {source}...")

        # Запускаем обновление
        updated_count = updater.run_update(source)

        if updated_count > 0:
            print(
                f"Update successful. Total rates updated: {updated_count}. Last refresh: {datetime.now().isoformat()}")
            return 0
        else:
            print("Update completed with errors. Check logs/parser.log for details.")
            return 1

    except ImportError as e:
        print(f"ERROR: Parser Service not available: {e}")
        print("INFO: Using mock update...")
        return mock_update_rates()
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1


def mock_update_rates():
    """Мок-обновление курсов для тестирования"""
    from ..infra.database import DatabaseManager
    from datetime import datetime

    print("INFO: Using mock update (no real API calls)...")

    now = datetime.now().isoformat()

    # Создаем реалистичные тестовые данные
    rates_data = {
        "pairs": {
            "EUR_USD": {"rate": 0.92, "updated_at": now, "source": "MockService"},
            "BTC_USD": {"rate": 62345.67, "updated_at": now, "source": "MockService"},
            "ETH_USD": {"rate": 3456.78, "updated_at": now, "source": "MockService"},
            "RUB_USD": {"rate": 0.0105, "updated_at": now, "source": "MockService"},
            "GBP_USD": {"rate": 1.25, "updated_at": now, "source": "MockService"},
            "JPY_USD": {"rate": 0.0067, "updated_at": now, "source": "MockService"},
            "CNY_USD": {"rate": 0.14, "updated_at": now, "source": "MockService"},
            "USD_USD": {"rate": 1.0, "updated_at": now, "source": "System"},
        },
        "last_refresh": now,
        "source": "MockService"
    }

    # Сохраняем
    db = DatabaseManager()
    db.save_rates(rates_data)

    print("INFO: Mock rates updated successfully")
    print(f"Update successful. Total rates updated: {len(rates_data['pairs'])}. Last refresh: {now}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="ValutaTrade Hub - Валютный кошелек")
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')

    # register
    register_parser = subparsers.add_parser('register', help='Регистрация нового пользователя')
    register_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
    register_parser.add_argument('--password', type=str, required=True, help='Пароль')

    # login
    login_parser = subparsers.add_parser('login', help='Вход в систему')
    login_parser.add_argument('--username', type=str, required=True, help='Имя пользователя')
    login_parser.add_argument('--password', type=str, required=True, help='Пароль')

    # show-portfolio
    portfolio_parser = subparsers.add_parser('show-portfolio', help='Показать портфель')
    portfolio_parser.add_argument('--base', type=str, default='USD', help='Базовая валюта (по умолчанию USD)')

    # buy
    buy_parser = subparsers.add_parser('buy', help='Купить валюту')
    buy_parser.add_argument('--currency', type=str, required=True, help='Код покупаемой валюты')
    buy_parser.add_argument('--amount', type=float, required=True, help='Количество покупаемой валюты')

    # sell
    sell_parser = subparsers.add_parser('sell', help='Продать валюту')
    sell_parser.add_argument('--currency', type=str, required=True, help='Код продаваемой валюты')
    sell_parser.add_argument('--amount', type=float, required=True, help='Количество продаваемой валюты')

    # get-rate
    rate_parser = subparsers.add_parser('get-rate', help='Получить курс валюты')
    rate_parser.add_argument('--from', type=str, required=True, dest='from_currency', help='Исходная валюта')
    rate_parser.add_argument('--to', type=str, required=True, dest='to_currency', help='Целевая валюта')

    # update-rates
    subparsers.add_parser('update-rates', help='Обновить курсы валют')

    # show-rates
    show_rates_parser = subparsers.add_parser('show-rates', help='Показать курсы валют')
    show_rates_parser.add_argument('--currency', type=str, help='Показать курс только для указанной валюты')
    show_rates_parser.add_argument('--top', type=int, help='Показать N самых дорогих криптовалют')
    show_rates_parser.add_argument('--base', type=str, help='Показать все курсы относительно указанной базы')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'register':
            return handle_register(args.username, args.password)
        elif args.command == 'login':
            return handle_login(args.username, args.password)
        elif args.command == 'show-portfolio':
            return handle_show_portfolio(args.base)
        elif args.command == 'buy':
            return handle_buy(args.currency, args.amount)
        elif args.command == 'sell':
            return handle_sell(args.currency, args.amount)
        elif args.command == 'get-rate':
            return handle_get_rate(args.from_currency, args.to_currency)
        elif args.command == 'update-rates':
            return handle_update_rates()
        elif args.command == 'show-rates':
            return handle_show_rates(args.currency, args.top, args.base)
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return 1

    return 0


def handle_register(username: str, password: str) -> int:
    try:
        user = UserUseCases.register(username, password)
        print(
            f"Пользователь '{username}' зарегистрирован (id={user.user_id}). Войдите: login --username {username} --password [ваш пароль]")
        return 0
    except ValueError as e:
        print(str(e))
        return 1


def handle_login(username: str, password: str) -> int:
    try:
        UserUseCases.login(username, password)
        print(f"Вы вошли как '{username}'")
        return 0
    except ValueError as e:
        print(str(e))
        return 1


def handle_show_portfolio(base_currency: str) -> int:
    if not SessionManager.is_logged_in():
        print("Сначала выполните login")
        return 1

    user = SessionManager.get_current_user()
    portfolio = PortfolioUseCases.get_portfolio(user.user_id)

    if not portfolio.wallets:
        print("Портфель пуст")
        return 0

    print(f"Портфель пользователя '{user.username}' (база: {base_currency}):")

    total_value = 0
    for currency_code, wallet in portfolio.wallets.items():
        # Временная заглушка для конвертации
        exchange_rates = {
            "EUR_USD": 1.0786,
            "BTC_USD": 59337.21,
            "RUB_USD": 0.01016,
            "ETH_USD": 3720.00,
            "USD_USD": 1.0
        }

        rate_key = f"{currency_code}_{base_currency}"
        if rate_key in exchange_rates:
            rate = exchange_rates[rate_key]
            value = wallet.balance * rate
            total_value += value
            print(f"- {currency_code}: {wallet.balance:.2f} → {value:.2f} {base_currency}")
        elif currency_code == base_currency:
            total_value += wallet.balance
            print(f"- {currency_code}: {wallet.balance:.2f} → {wallet.balance:.2f} {base_currency}")

    print(f"\nИТОГО: {total_value:,.2f} {base_currency}")
    return 0


def handle_buy(currency: str, amount: float) -> int:
    if not SessionManager.is_logged_in():
        print("Сначала выполните login")
        return 1

    if amount <= 0:
        print("'amount' должен быть положительным числом")
        return 1

    try:
        user = SessionManager.get_current_user()
        portfolio, rate = PortfolioUseCases.buy_currency(user.user_id, currency.upper(), amount)

        estimated_cost = amount * rate

        print(f"Покупка выполнена: {amount:.4f} {currency} по курсу ${rate:.2f} USD/{currency}")
        print("\nИзменения в портфеле:")

        wallet = portfolio.get_wallet(currency.upper())
        print(f"- {currency}: было 0.0000 → стало {wallet.balance:.4f}")
        print(f"Оценочная стоимость покупки: {estimated_cost:,.2f} USD")

        return 0
    except ValueError as e:
        print(str(e))
        return 1


def handle_sell(currency: str, amount: float) -> int:
    if not SessionManager.is_logged_in():
        print("Сначала выполните login")
        return 1

    if amount <= 0:
        print("'amount' должен быть положительным числом")
        return 1

    try:
        user = SessionManager.get_current_user()
        portfolio, rate = PortfolioUseCases.sell_currency(user.user_id, currency.upper(), amount)

        estimated_revenue = amount * rate

        print(f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}")
        print("\nИзменения в портфеле:")

        wallet = portfolio.get_wallet(currency.upper())
        if wallet:
            print(f"- {currency}: было {wallet.balance + amount:.4f} → стало {wallet.balance:.4f}")
        else:
            print(f"- {currency}: было {amount:.4f} → стало 0.0000")

        print(f"Оценочная выручка: {estimated_revenue:,.2f} USD")

        return 0

    except InsufficientFundsError as e:
        print(str(e))
        return 1
    except CurrencyNotFoundError:
        print(f"Неизвестная валюта '{currency}'. Используйте команду 'get-rate' для проверки доступных валют.")
        return 1
    except ValueError as e:
        if "устарел" in str(e):
            print(str(e))
            print("Выполните команду: update-rates")
        else:
            print(f"Ошибка: {str(e)}")
        return 1


def handle_get_rate(from_currency: str, to_currency: str) -> int:
    try:
        rate, updated_at = RatesUseCases.get_rate(
            from_currency.upper(),
            to_currency.upper()
        )

        reverse_rate = 1 / rate if rate != 0 else 0

        print(f"Курс {from_currency.upper()}={to_currency.upper()}: {rate:.6f} (обновлено: {updated_at})")
        print(f"Обратный курс {to_currency.upper()}={from_currency.upper()}: {reverse_rate:.6f}")

        return 0
    except ValueError:
        print(f"Курс {from_currency.upper()}={to_currency.upper()} недоступен. Повторите попытку позже...")
        return 1


def handle_show_rates(currency: str = None, top: int = None, base: str = None) -> int:
    from ..infra.database import DatabaseManager

    db = DatabaseManager()
    rates = db.load_rates()

    if not rates.get("pairs"):
        print("Локальный кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
        return 1

    pairs = rates["pairs"]

    if currency:
        filtered_pairs = {k: v for k, v in pairs.items() if currency.upper() in k}
        if not filtered_pairs:
            print(f"Курс для '{currency}' не найден в кеше.")
            return 1
        pairs = filtered_pairs

    print(f"Rates from cache (updated at {rates.get('last_refresh', 'N/A')}):")

    sorted_pairs = sorted(pairs.items())
    if top:
        sorted_pairs = sorted(pairs.items(), key=lambda x: x[1]["rate"], reverse=True)[:top]

    for pair, data in sorted_pairs:
        print(f"  - {pair}: {data['rate']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
