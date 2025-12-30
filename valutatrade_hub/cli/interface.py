import argparse
import os
import sys
from prettytable import PrettyTable
from datetime import datetime

from ..core.usecases import UserManager, PortfolioManager
from ..core.exceptions import (
    InsufficientFundsError, CurrencyNotFoundError, ApiRequestError,
    UserNotFoundError, InvalidPasswordError, WalletNotFoundError,
    InvalidAmountError, AuthenticationError
)
from ..core.utils import format_currency
from ..infra.settings import settings
from ..parser_service import updater, storage, scheduler
from ..parser_service.config import config
from ..logging_config import setup_logging

# Настройка логирования при запуске CLI
setup_logging()


class CLIInterface:
    """Командный интерфейс приложения"""

    def __init__(self):
        self.user_manager = UserManager()
        self.portfolio_manager = PortfolioManager(self.user_manager)
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Создание парсера аргументов"""
        parser = argparse.ArgumentParser(
            description="Валютный кошелёк - управление виртуальным портфелем валют",
            epilog="Пример: python main.py buy --currency BTC --amount 0.1"
        )
        subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

        # ========== ОСНОВНЫЕ КОМАНДЫ ==========

        # Команда register
        register_parser = subparsers.add_parser("register", help="Регистрация нового пользователя")
        register_parser.add_argument("--username", required=True, help="Имя пользователя")
        register_parser.add_argument("--password", required=True, help="Пароль (минимум 4 символа)")

        # Команда login
        login_parser = subparsers.add_parser("login", help="Вход в систему")
        login_parser.add_argument("--username", required=True, help="Имя пользователя")
        login_parser.add_argument("--password", required=True, help="Пароль")

        # Команда logout
        subparsers.add_parser("logout", help="Выход из системы")

        # Команда show-portfolio
        portfolio_parser = subparsers.add_parser("show-portfolio", help="Показать портфель")
        portfolio_parser.add_argument("--base", default="USD",
                                      help="Базовая валюта (по умолчанию USD)")

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

        # ========== КОМАНДЫ ПАРСЕРА ==========

        # Команда update-rates
        update_parser = subparsers.add_parser("update-rates",
                                              help="Обновить курсы валют из внешних API")
        update_parser.add_argument("--source",
                                   choices=["coingecko", "exchangerate", "mock", "all"],
                                   default="all",
                                   help="Источник данных (по умолчанию: все)")
        update_parser.add_argument("--force", action="store_true",
                                   help="Принудительное обновление (игнорировать свежесть кэша)")

        # Команда show-rates
        show_rates_parser = subparsers.add_parser("show-rates",
                                                  help="Показать курсы валют из кэша")
        show_rates_parser.add_argument("--currency",
                                       help="Показать курсы только для указанной валюты")
        show_rates_parser.add_argument("--top", type=int,
                                       help="Показать N самых дорогих криптовалют")
        show_rates_parser.add_argument("--base", default="USD",
                                       help="Базовая валюта (по умолчанию: USD)")
        show_rates_parser.add_argument("--history", action="store_true",
                                       help="Показать историю курсов вместо текущих значений")
        show_rates_parser.add_argument("--limit", type=int, default=10,
                                       help="Лимит исторических записей (по умолчанию: 10)")

        # Команда scheduler
        scheduler_parser = subparsers.add_parser("scheduler",
                                                 help="Управление планировщиком обновлений")
        scheduler_parser.add_argument("action",
                                      choices=["start", "stop", "status", "run-once"],
                                      help="Действие с планировщиком")
        scheduler_parser.add_argument("--interval", type=int,
                                      help="Интервал в минутах (для команды start)")
        scheduler_parser.add_argument("--foreground", action="store_true",
                                      help="Запуск в foreground (не в фоне)")

        # Команда cache
        cache_parser = subparsers.add_parser("cache",
                                             help="Управление кэшем курсов")
        cache_parser.add_argument("action",
                                  choices=["clear", "status", "info"],
                                  help="Действие с кэшем")

        # Команда config
        config_parser = subparsers.add_parser("config",
                                              help="Показать конфигурацию парсера")
        config_parser.add_argument("--section",
                                   choices=["api", "currencies", "paths", "all"],
                                   default="all",
                                   help="Раздел конфигурации")

        return parser

    def run(self):
        """Запуск CLI"""
        if len(sys.argv) == 1:
            self.parser.print_help()
            return

        args = self.parser.parse_args()

        try:
            # Существующие команды...

            # Новые команды парсера
            if args.command == "update-rates":
                self.handle_update_rates(args)
            elif args.command == "show-rates":
                self.handle_show_rates(args)
            elif args.command == "scheduler":
                self.handle_scheduler(args)
            elif args.command == "cache":
                self.handle_cache(args)
            elif args.command == "config":
                self.handle_config(args)
            else:
                # Обработка существующих команд...
                pass

        except Exception as e:
            self.handle_error(e)

    def handle_update_rates(self, args):
        """Обработка команды update-rates"""
        print("🔄 Обновление курсов валют...")
        print(f"   Источник: {args.source}")

        try:
            if args.force:
                result = updater.force_update()
                print("   Режим: принудительное обновление")
            else:
                result = updater.run_update(source=args.source)
                print("   Режим: обычное обновление")

            if result.get("success", False):
                print(f"✅ Обновление успешно завершено!")
                print(f"   Обновлено курсов: {result.get('total_rates', 0)}")
                print(f"   Время обновления: {result.get('last_refresh', 'N/A')}")

                # Показываем статистику по источникам
                sources = result.get("sources", {})
                for source_name, source_stat in sources.items():
                    status = source_stat.get("status", "unknown")
                    if status == "success":
                        print(f"   {source_name}: ✓ {source_stat.get('rates_count', 0)} курсов")
                    else:
                        print(f"   {source_name}: ✗ {source_stat.get('error', 'Ошибка')}")

                if result.get("errors"):
                    print(f"   Предупреждения: {len(result['errors'])} ошибок")
                    for error in result["errors"][:3]:  # Показываем только первые 3
                        print(f"     - {error[:60]}...")

            else:
                print("⚠️  Обновление завершено без данных")
                if result.get("errors"):
                    print("   Ошибки:")
                    for error in result["errors"]:
                        print(f"     - {error}")

        except Exception as e:
            print(f"❌ Ошибка при обновлении курсов: {e}")
            print("   Проверьте:")
            print("   1. Подключение к интернету")
            print("   2. Корректность API ключа (если используется ExchangeRate-API)")
            print("   3. Файл config.py в директории parser_service")

    def handle_show_rates(self, args):
        """Обработка команды show-rates"""
        if args.history:
            self._show_rates_history(args)
        else:
            self._show_current_rates(args)

    def _show_current_rates(self, args):
        """Показать текущие курсы из кэша"""
        # Загружаем текущие курсы
        data = storage.load_current_rates()
        pairs = data.get("pairs", {})
        last_refresh = data.get("last_refresh")

        if not pairs:
            print("📭 Кэш курсов пуст")
            print("   Используйте команду: update-rates")
            return

        # Фильтруем по валюте, если указана
        filtered_pairs = {}
        if args.currency:
            currency = args.currency.upper()
            for pair_key, pair_data in pairs.items():
                if pair_data.get("from_currency") == currency or \
                        pair_data.get("to_currency") == currency:
                    filtered_pairs[pair_key] = pair_data
        else:
            filtered_pairs = pairs

        if not filtered_pairs:
            print(f"📭 Курсы для валюты '{args.currency}' не найдены")
            return

        # Сортируем
        sorted_pairs = sorted(
            filtered_pairs.items(),
            key=lambda x: x[1].get("rate", 0),
            reverse=True  # Самые дорогие сначала
        )

        # Применяем топ-N фильтр для криптовалют
        if args.top and not args.currency:
            crypto_pairs = [(k, v) for k, v in sorted_pairs
                            if v.get("from_currency") in config.CRYPTO_CURRENCIES]
            sorted_pairs = crypto_pairs[:args.top]

        # Создаем таблицу
        table = PrettyTable()
        table.field_names = ["Пара", "Курс", "Обновлено", "Источник"]
        table.align["Пара"] = "l"
        table.align["Курс"] = "r"
        table.align["Обновлено"] = "l"
        table.align["Источник"] = "l"

        for pair_key, pair_data in sorted_pairs:
            rate = pair_data.get("rate", 0)
            updated_at = pair_data.get("updated_at", "N/A")
            source = pair_data.get("source", "N/A")

            # Форматируем время
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                updated_str = dt.strftime("%H:%M:%S")
            except:
                updated_str = updated_at[:19]

            # Форматируем курс
            if rate >= 1000:
                rate_str = f"{rate:,.2f}"
            elif rate >= 1:
                rate_str = f"{rate:.4f}"
            elif rate >= 0.001:
                rate_str = f"{rate:.6f}"
            else:
                rate_str = f"{rate:.8f}"

            table.add_row([pair_key, rate_str, updated_str, source])

        # Выводим результат
        print(f"📊 Текущие курсы валют (база: {args.base})")
        if last_refresh:
            try:
                dt = datetime.fromisoformat(last_refresh.replace('Z', '+00:00'))
                print(f"   Обновлено: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except:
                print(f"   Обновлено: {last_refresh}")

        print(f"   Всего пар: {len(pairs)}")
        if args.currency:
            print(f"   Фильтр: {args.currency}")
        if args.top:
            print(f"   Топ: {args.top} криптовалют")

        print(table)

        # Показываем свежесть кэша
        if storage.is_cache_fresh():
            print("   ✅ Кэш актуален")
        else:
            print("   ⚠️  Кэш устарел, рекомендуется обновить:")
            print("      update-rates")

    def _show_rates_history(self, args):
        """Показать историю курсов"""
        # Загружаем историю
        history = storage.load_history(
            limit=args.limit,
            currency=args.currency
        )

        if not history:
            print("📭 История курсов пуста")
            print("   Используйте команду: update-rates")
            return

        # Создаем таблицу
        table = PrettyTable()
        table.field_names = ["Время", "Пара", "Курс", "Источник", "ID"]
        table.align["Время"] = "l"
        table.align["Пара"] = "l"
        table.align["Курс"] = "r"
        table.align["Источник"] = "l"
        table.align["ID"] = "l"
        table.max_width["ID"] = 20

        for record in history:
            timestamp = record.get("timestamp", "")
            from_curr = record.get("from_currency", "")
            to_curr = record.get("to_currency", "")
            rate = record.get("rate", 0)
            source = record.get("source", "")
            record_id = record.get("id", "")[:20]

            # Форматируем время
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M:%S")
                date_str = dt.strftime("%Y-%m-%d")
            except:
                time_str = timestamp[:19]
                date_str = timestamp[:10]

            # Форматируем курс
            if rate >= 1000:
                rate_str = f"{rate:,.2f}"
            elif rate >= 1:
                rate_str = f"{rate:.4f}"
            elif rate >= 0.001:
                rate_str = f"{rate:.6f}"
            else:
                rate_str = f"{rate:.8f}"

            table.add_row([
                f"{date_str}\n{time_str}",
                f"{from_curr} → {to_curr}",
                rate_str,
                source,
                f"...{record_id[-15:]}" if len(record_id) > 20 else record_id
            ])

        # Выводим результат
        print(f"📜 История курсов валют")
        print(f"   Всего записей: {len(history)}")
        if args.currency:
            print(f"   Фильтр: {args.currency}")
        if args.limit != 10:
            print(f"   Лимит: {args.limit}")

        print(table)

    def handle_scheduler(self, args):
        """Обработка команды scheduler"""
        action = args.action

        if action == "start":
            print("🚀 Запуск планировщика...")

            interval = args.interval or config.SCHEDULER_INTERVAL_MINUTES
            foreground = args.foreground

            scheduler.change_interval(interval)
            scheduler.start(background=not foreground)

            status = scheduler.get_status()
            print(f"✅ Планировщик запущен")
            print(f"   Интервал: {interval} минут")
            print(f"   Режим: {'foreground' if foreground else 'background'}")

            next_run = status.get("next_run")
            if next_run:
                print(f"   Следующее обновление: {next_run}")

        elif action == "stop":
            print("🛑 Остановка планировщика...")
            scheduler.stop()
            print("✅ Планировщик остановлен")

        elif action == "status":
            print("📊 Статус планировщика:")
            status = scheduler.get_status()

            for key, value in status.items():
                if key == "next_run" and value:
                    print(f"   {key}: {value}")
                else:
                    print(f"   {key}: {value}")

            if status.get("running"):
                print("   ✅ Планировщик активен")
            else:
                print("   ⏸️  Планировщик остановлен")

        elif action == "run-once":
            print("⚡ Запуск разового обновления...")
            result = scheduler.run_once()

            if result.get("success", False):
                print(f"✅ Обновление успешно")
                print(f"   Курсов обновлено: {result.get('total_rates', 0)}")
            else:
                print("⚠️  Обновление завершилось с ошибками")

    def handle_cache(self, args):
        """Обработка команды cache"""
        action = args.action

        if action == "clear":
            print("🧹 Очистка кэша...")
            storage.clear_cache()
            print("✅ Кэш очищен")

        elif action == "status":
            print("📊 Статус кэша:")

            data = storage.load_current_rates()
            pairs_count = len(data.get("pairs", {}))
            last_refresh = data.get("last_refresh")

            print(f"   Курсов в кэше: {pairs_count}")
            print(f"   Последнее обновление: {last_refresh or 'N/A'}")

            if storage.is_cache_fresh():
                print("   ✅ Кэш актуален")
            else:
                print("   ⚠️  Кэш устарел")
                print("   Рекомендация: update-rates")

        elif action == "info":
            print("ℹ️  Информация о кэше:")

            # Размер файлов
            import os
            rates_size = os.path.getsize(config.RATES_FILE_PATH) if config.RATES_FILE_PATH.exists() else 0
            history_size = os.path.getsize(config.HISTORY_FILE_PATH) if config.HISTORY_FILE_PATH.exists() else 0

            print(f"   Файл кэша: {config.RATES_FILE_PATH}")
            print(f"   Размер: {rates_size / 1024:.1f} KB")
            print(f"   Файл истории: {config.HISTORY_FILE_PATH}")
            print(f"   Размер: {history_size / 1024:.1f} KB")
            print(f"   TTL кэша: {config.CACHE_TTL_SECONDS} секунд")

    def handle_config(self, args):
        """Обработка команды config"""
        section = args.section

        print("⚙️  Конфигурация парсер-сервиса:")
        print("=" * 60)

        if section in ["api", "all"]:
            print("\nAPI Настройки:")
            print(
                f"   ExchangeRate-API Key: {'***' + config.EXCHANGERATE_API_KEY[-4:] if config.EXCHANGERATE_API_KEY else 'не задан'}")
            print(f"   CoinGecko URL: {config.COINGECKO_URL}")
            print(f"   ExchangeRate-API URL: {config.EXCHANGERATE_API_URL}")
            print(f"   Таймаут запроса: {config.REQUEST_TIMEOUT} сек")
            print(f"   Попыток повторения: {config.REQUEST_RETRIES}")

        if section in ["currencies", "all"]:
            print("\nВалюты:")
            print(f"   Базовая валюта: {config.BASE_CURRENCY}")
            print(f"   Фиатные валюты ({len(config.FIAT_CURRENCIES)}): {', '.join(config.FIAT_CURRENCIES)}")
            print(f"   Криптовалюты ({len(config.CRYPTO_CURRENCIES)}): {', '.join(config.CRYPTO_CURRENCIES)}")
            print(f"   Сопоставление ID: {len(config.CRYPTO_ID_MAP)} пар")

        if section in ["paths", "all"]:
            print("\nПути:")
            print(f"   Файл кэша: {config.RATES_FILE_PATH}")
            print(f"   Файл истории: {config.HISTORY_FILE_PATH}")
            print(f"   Директория данных: {config.DATA_DIR}")
            print(f"   Директория логов: {config.LOG_DIR}")

        print("=" * 60)

        # Показываем переменные окружения
        api_key = os.getenv("EXCHANGERATE_API_KEY")
        if api_key:
            print(f"\nℹ️  API ключ загружен из переменной окружения")
        else:
            print(f"\n⚠️  API ключ не найден в переменных окружения")
            print("   Чтобы задать ключ, выполните:")
            print("   export EXCHANGERATE_API_KEY='ваш_ключ'")
            print("   Или добавьте в ~/.bashrc / ~/.zshrc")