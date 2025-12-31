import sys
import json
import os
from datetime import datetime
from valutatrade_hub.cli.interface import main as cli_main


class FinalTester:
    def __init__(self):
        self.test_results = []
        self.setup_test_environment()

    def run_command(self, args_list, expected_error=None, check_output=None):
        """Запустить команду и проверить результат"""
        print(f"\n▶ КОМАНДА: {' '.join(args_list)}")
        if expected_error:
            print(f"  ОЖИДАЕМ ОШИБКУ: {expected_error}")

        original_argv = sys.argv
        try:
            sys.argv = ['project'] + args_list
            result = cli_main()

            if expected_error:
                # Проверяем что была ошибка
                if result == 0:
                    self.record_fail(f"Ожидалась ошибка: {expected_error}")
                    return False
                else:
                    self.record_success("Получена ожидаемая ошибка")
                    return True
            else:
                # Проверяем что успех
                if result != 0:
                    self.record_fail(f"Команда завершилась с ошибкой: {result}")
                    return False
                else:
                    self.record_success("Команда выполнена успешно")
                    return True

        except Exception as e:
            error_msg = str(e)
            if expected_error and expected_error in error_msg:
                self.record_success(f"Получена ожидаемая ошибка: {error_msg}")
                return True
            else:
                self.record_fail(f"Неожиданная ошибка: {error_msg}")
                return False
        finally:
            sys.argv = original_argv

    def record_success(self, message):
        """Записать успешный тест"""
        self.test_results.append(("✅ OK", message))
        print(f"  ✅ {message}")

    def record_fail(self, message):
        """Записать проваленный тест"""
        self.test_results.append(("❌ FAIL", message))
        print(f"  ❌ {message}")

    def setup_test_environment(self):
        """Подготовить тестовое окружение"""
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        self.clear_all_data()
        self.create_fresh_rates()

    def clear_all_data(self):
        """Очистить все данные"""
        for file in ['session.json', 'users.json', 'portfolios.json']:
            try:
                with open(f'data/{file}', 'w') as f:
                    if file == 'session.json':
                        json.dump({}, f)
                    else:
                        json.dump([], f)
            except: # noqa
                pass

    def create_fresh_rates(self):
        """Создать свежие курсы"""
        now = datetime.now().isoformat()
        rates_data = {
            "pairs": {
                "EUR_USD": {"rate": 0.92, "updated_at": now, "source": "ParserService"},
                "BTC_USD": {"rate": 62345.67, "updated_at": now, "source": "ParserService"},
                "ETH_USD": {"rate": 3456.78, "updated_at": now, "source": "ParserService"},
                "RUB_USD": {"rate": 0.0105, "updated_at": now, "source": "ParserService"},
            },
            "last_refresh": now,
            "source": "ParserService"
        }
        with open('data/rates.json', 'w', encoding='utf-8') as f:
            json.dump(rates_data, f, indent=2)

    def force_logout(self):
        """Принудительный выход"""
        with open('data/session.json', 'w') as f:
            json.dump({}, f)

    def run_test_suite(self, name, test_func):
        """Запустить набор тестов"""
        print(f"\n{'=' * 60}")
        print(f"ТЕСТ: {name}")
        print(f"{'=' * 60}")
        test_func()

    def test_1_registration(self):
        """Тест регистрации"""
        # Успешная регистрация
        self.run_command(['register', '--username', 'alice', '--password', '1234'])

        # Ошибка: имя занято
        self.run_command(
            ['register', '--username', 'alice', '--password', '1234'],
            expected_error="Имя пользователя 'alice' уже занято"
        )

        # Ошибка: короткий пароль
        self.run_command(
            ['register', '--username', 'bob', '--password', '123'],
            expected_error="Пароль должен быть не короче 4 символов"
        )

    def test_2_authentication(self):
        """Тест аутентификации"""
        # Успешный вход
        self.run_command(['login', '--username', 'alice', '--password', '1234'])

        # Ошибка: неверный пароль
        self.run_command(
            ['login', '--username', 'alice', '--password', 'wrong'],
            expected_error="Неверный пароль"
        )

        # Ошибка: пользователь не найден
        self.run_command(
            ['login', '--username', 'nonexistent', '--password', '1234'],
            expected_error="Пользователь 'nonexistent' не найден"
        )

    def test_3_portfolio_auth(self):
        """Тест авторизации для портфеля"""
        # Ошибка: не залогинен
        self.force_logout()
        self.run_command(
            ['show-portfolio'],
            expected_error="Сначала выполните login"
        )

        # Входим
        self.run_command(['login', '--username', 'alice', '--password', '1234'])

        # Пустой портфель
        self.run_command(['show-portfolio'])  # "Портфель пуст"

    def test_4_buy_operations(self):
        """Тест операций покупки"""
        # Ошибка: отрицательная сумма
        self.run_command(
            ['buy', '--currency', 'BTC', '--amount', '-0.1'],
            expected_error="'amount' должен быть положительным"
        )

        # Ошибка: неизвестная валюта
        self.run_command(
            ['buy', '--currency', 'XYZ', '--amount', '10'],
            expected_error="Неизвестная валюта 'XYZ'"
        )

        # Успешная покупка BTC
        self.run_command(['buy', '--currency', 'BTC', '--amount', '0.01'])

        # Показать портфель
        self.run_command(['show-portfolio'])

    def test_5_sell_operations(self):
        """Тест операций продажи"""
        # Ошибка: продажа несуществующей валюты
        self.run_command(
            ['sell', '--currency', 'EUR', '--amount', '100'],
            expected_error="нет кошелька 'EUR'"
        )

        # Ошибка: недостаточно средств
        self.run_command(
            ['sell', '--currency', 'BTC', '--amount', '1'],
            expected_error="Недостаточно средств"
        )

        # Успешная продажа
        self.run_command(['sell', '--currency', 'BTC', '--amount', '0.005'])

        # Финальный портфель
        self.run_command(['show-portfolio'])

    def test_6_rate_operations(self):
        """Тест операций с курсами"""
        # Получить курс
        self.run_command(['get-rate', '--from', 'USD', '--to', 'BTC'])

        # Обратный курс
        self.run_command(['get-rate', '--from', 'BTC', '--to', 'USD'])

        # Ошибка: неизвестная валюта
        self.run_command(
            ['get-rate', '--from', 'USD', '--to', 'XYZ'],
            expected_error="недоступен"
        )

        # Показать все курсы
        self.run_command(['show-rates'])

        # Показать топ-2
        self.run_command(['show-rates', '--top', '2'])

        # Показать для конкретной валюты
        self.run_command(['show-rates', '--currency', 'BTC'])

    def test_7_update_rates(self):
        """Тест обновления курсов"""
        # Обновить курсы
        self.run_command(['update-rates'])

        # Показать обновленные курсы
        self.run_command(['show-rates'])

    def test_8_full_workflow_tz(self):
        """Полный рабочий процесс как в ТЗ"""
        print("\n📋 СЦЕНАРИЙ ИЗ ТЕХНИЧЕСКОГО ЗАДАНИЯ:")

        # 1. Регистрация нового пользователя
        self.run_command(['register', '--username', 'test_user', '--password', 'mypass'])

        # 2. Вход
        self.run_command(['login', '--username', 'test_user', '--password', 'mypass'])

        # 3. Обновление курсов
        self.run_command(['update-rates'])

        # 4. Показать пустой портфель
        self.run_command(['show-portfolio'])

        # 5. Купить BTC (как в примере ТЗ)
        self.run_command(['buy', '--currency', 'BTC', '--amount', '0.05'])

        # 6. Показать портфель с BTC
        self.run_command(['show-portfolio'])

        # 7. Продать часть BTC
        self.run_command(['sell', '--currency', 'BTC', '--amount', '0.01'])

        # 8. Получить курс
        self.run_command(['get-rate', '--from', 'USD', '--to', 'BTC'])

        # 9. Показать топ курсов
        self.run_command(['show-rates', '--top', '2'])

    def run_all_tests(self):
        """Запустить все тесты"""
        print("\n" + "=" * 60)
        print("ПОЛНОЕ ТЕСТИРОВАНИЕ VALUTATRADE HUB")
        print("=" * 60)

        test_suites = [
            ("Регистрация", self.test_1_registration),
            ("Аутентификация", self.test_2_authentication),
            ("Портфель и авторизация", self.test_3_portfolio_auth),
            ("Операции покупки", self.test_4_buy_operations),
            ("Операции продажи", self.test_5_sell_operations),
            ("Работа с курсами", self.test_6_rate_operations),
            ("Обновление курсов", self.test_7_update_rates),
            ("Полный workflow (ТЗ)", self.test_8_full_workflow_tz),
        ]

        for name, test_func in test_suites:
            self.run_test_suite(name, test_func)

        self.print_results()

    def print_results(self):
        """Вывести результаты"""
        print(f"\n{'=' * 60}")
        print("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
        print(f"{'=' * 60}")

        total = len(self.test_results)
        passed = sum(1 for status, _ in self.test_results if "✅" in status)
        failed = total - passed

        print("\n📊 Статистика:")
        print(f"   Всего проверок: {total}")
        print(f"   Успешных: {passed}")
        print(f"   Проваленных: {failed}")

        if failed > 0:
            print("\n⚠ Проблемные проверки:")
            for i, (status, message) in enumerate(self.test_results, 1):
                if "❌" in status:
                    print(f"   {i}. {message}")

        print(f"\n{'=' * 60}")
        if failed == 0:
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"⚠ Найдено {failed} проблем")
            print("Требуются исправления")
        print(f"{'=' * 60}")


def main():
    tester = FinalTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()