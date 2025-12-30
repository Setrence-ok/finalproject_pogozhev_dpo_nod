import argparse
import sys
from prettytable import PrettyTable

from ..core.usecases import UserManager, PortfolioManager
from ..core.utils import format_currency


class CLIInterface:
    """Командный интерфейс приложения"""

    def __init__(self):
        self.user_manager = UserManager()
        self.portfolio_manager = PortfolioManager(self.user_manager)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Создание парсера аргументов"""
        parser = argparse.ArgumentParser(
            description="Валютный кошелёк - управление виртуальным портфелем валют"
        )
        subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

        # Команда register
        register_parser = subparsers.add_parser("register", help="Регистрация нового пользователя")
        register_parser.add_argument("--username", required=True, help="Имя пользователя")
        register_parser.add_argument("--password", required=True, help="Пароль")

        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument("--username", required=True, help="Имя пользователя")
        login_parser.add_argument("--password", required=True, help="Пароль")

        # Команда logout
        subparsers.add_parser("logout", help="Выход из системы")

        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser("show-portfolio", help="Показать портфель")
        portfolio_parser.add_argument("--base", default="USD", help="Базовая валюта (по умолчанию USD)")

        # Команда buy
        buy_parser = subparsers.add_parser("buy", help="Купить валюту")
        buy_parser.add_argument("--currency", required=True, help="Код валюты (например, BTC)")
        buy_parser.add_argument("--amount", type=float, required=True, help="Количество")

        # Команда sell
        sell_parser = subparsers.add_parser("sell", help="Продать валюту")
        sell_parser.add_argument("--currency", required=True, help="Код валюты")
        sell_parser.add_argument("--amount", type=float, required=True, help="Количество")

        # Команда get-rate
        rate_parser = subparsers.add_parser("get-rate", help="Получить курс валюты")
        rate_parser.add_argument("--from", dest="from_currency", required=True, help="Исходная валюта")
        rate_parser.add_argument("--to", dest="to_currency", required=True, help="Целевая валюта")

        return parser

    def run(self):
        """Запуск CLI"""
        if len(sys.argv) == 1:
            self.parser.print_help()
            return

        args = self.parser.parse_args()

        try:
            if args.command == "register":
                self.handle_register(args)
            elif args.command == "login":
                self.handle_login(args)
            elif args.command == "logout":
                self.handle_logout()
            elif args.command == "show-portfolio":
                self.handle_show_portfolio(args)
            elif args.command == "buy":
                self.handle_buy(args)
            elif args.command == "sell":
                self.handle_sell(args)
            elif args.command == "get-rate":
                self.handle_get_rate(args)
            else:
                self.parser.print_help()
        except Exception as e:
            print(f"Ошибка: {e}")

    def handle_register(self, args):
        """Обработка команды register"""
        try:
            user = self.user_manager.register(args.username, args.password)
            print(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}). "
                  f"Войдите: login --username {user.username} --password <ваш_пароль>")
        except ValueError as e:
            print(f"Ошибка регистрации: {e}")

    def handle_login(self, args):
        """Обработка команды login"""
        try:
            user = self.user_manager.login(args.username, args.password)
            print(f"Вы вошли как '{user.username}'")
        except ValueError as e:
            print(f"Ошибка входа: {e}")

    def handle_logout(self):
        """Обработка команды logout"""
        self.user_manager.logout()
        print("Вы вышли из системы")

    def handle_show_portfolio(self, args):
        """Обработка команды show-portfolio"""
        try:
            wallets_info, total_value = self.portfolio_manager.show_portfolio(args.base)

            if not wallets_info:
                print("Портфель пуст")
                return

            table = PrettyTable()
            table.field_names = ["Валюта", "Баланс", f"Стоимость ({args.base})"]
            table.align["Валюта"] = "l"
            table.align["Баланс"] = "r"
            table.align[f"Стоимость ({args.base})"] = "r"

            for currency, info in wallets_info.items():
                table.add_row([
                    currency,
                    format_currency(info["balance"], currency),
                    format_currency(info["value_in_base"], args.base)
                ])

            print(f"Портфель пользователя (база: {args.base}):")
            print(table)
            print(f"\nИТОГО: {format_currency(total_value, args.base)}")

        except ValueError as e:
            print(f"Ошибка: {e}")

    def handle_buy(self, args):
        """Обработка команды buy"""
        try:
            result = self.portfolio_manager.buy_currency(args.currency, args.amount)

            # Получение курса для отображения
            try:
                rate_data = self.portfolio_manager.get_exchange_rate(args.currency, "USD")
                rate = rate_data["rate"]
            except ValueError:
                rate = 0

            print("Покупка выполнена успешно!")
            print(f"Куплено: {result['amount']} {result['currency']}")
            print(f"Новый баланс: {result['new_balance']} {result['currency']}")
            if rate > 0:
                print(f"Курс покупки: {rate:,.2f} USD/{args.currency}")
                print(f"Оценочная стоимость: {format_currency(result['cost_usd'])}")

        except ValueError as e:
            print(f"Ошибка покупки: {e}")

    def handle_sell(self, args):
        """Обработка команды sell"""
        try:
            result = self.portfolio_manager.sell_currency(args.currency, args.amount)

            # Получение курса для отображения
            try:
                rate_data = self.portfolio_manager.get_exchange_rate(args.currency, "USD")
                rate = rate_data["rate"]
            except ValueError:
                rate = 0

            print("Продажа выполнена успешно!")
            print(f"Продано: {result['amount']} {result['currency']}")
            print(f"Новый баланс: {result['new_balance']} {result['currency']}")
            if rate > 0:
                print(f"Курс продажи: {rate:,.2f} USD/{args.currency}")
                print(f"Оценочная выручка: {format_currency(result['revenue_usd'])}")

        except ValueError as e:
            print(f"Ошибка продажи: {e}")

    def handle_get_rate(self, args):
        """Обработка команды get-rate"""
        try:
            rate_data = self.portfolio_manager.get_exchange_rate(
                args.from_currency, args.to_currency
            )

            print(f"Курс {rate_data['from']}-{rate_data['to']}: {rate_data['rate']:.8f}")
            print(f"Обновлено: {rate_data['updated_at']}")

            # Вывод обратного курса
            if rate_data['rate'] != 0:
                reverse_rate = 1 / rate_data['rate']
                print(f"Обратный курс {rate_data['to']}-{rate_data['from']}: {reverse_rate:.8f}")

        except ValueError as e:
            print(f"Ошибка: {e}")