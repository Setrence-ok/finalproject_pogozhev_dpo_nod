#!/usr/bin/env python3
"""
ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ ПРОЕКТА
Показывает работу всех функций с явным выводом
"""

import subprocess
import time
import os


def run_and_show(command, delay=1):
    """Запуск команды с явным выводом"""
    print(f"\n🚀 {' '.join(command)}")
    print("─" * 50)

    # Запускаем команду
    result = subprocess.run(command, capture_output=True, text=True)

    # Показываем ВЕСЬ вывод
    if result.stdout:
        print("📋 ВЫВОД:")
        print(result.stdout)

    if result.stderr:
        print("⚠️  ОШИБКИ/ПРЕДУПРЕЖДЕНИЯ:")
        print(result.stderr[:500])  # Ограничиваем вывод ошибок

    print(f"📊 Код завершения: {result.returncode}")
    print("─" * 50)

    time.sleep(delay)
    return result


def main():
    """Основная демонстрация"""
    print("🎬 ФИНАЛЬНАЯ ДЕМОНСТРАЦИЯ VALUTATRADE HUB")
    print("=" * 60)

    # Очищаем данные
    if os.path.exists("data"):
        for file in os.listdir("data"):
            if file.endswith(".json"):
                os.remove(f"data/{file}")

    print("\n1. 📋 ПОМОЩЬ И ДОСТУПНЫЕ КОМАНДЫ")
    run_and_show(["python", "main.py", "--help"], 2)

    print("\n2. 👤 РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ")
    run_and_show(["python", "main.py", "register",
                  "--username", "trader",
                  "--password", "SecureTrade123"], 1)

    print("\n3. 🔐 ВХОД В СИСТЕМУ")
    run_and_show(["python", "main.py", "login",
                  "--username", "trader",
                  "--password", "SecureTrade123"], 1)

    print("\n4. 💱 ОБНОВЛЕНИЕ КУРСОВ ВАЛЮТ")
    run_and_show(["python", "main.py", "update-rates", "--source", "mock"], 2)

    print("\n5. 📊 ПРОСМОТР КУРСОВ")
    run_and_show(["python", "main.py", "show-rates", "--top", "3"], 2)

    print("\n6. 💰 ПОПОЛНЕНИЕ СЧЕТА")
    run_and_show(["python", "main.py", "buy",
                  "--currency", "USD",
                  "--amount", "5000"], 1)

    print("\n7. 🟠 ПОКУПКА BITCOIN")
    run_and_show(["python", "main.py", "buy",
                  "--currency", "BTC",
                  "--amount", "0.1"], 1)

    print("\n8. 💶 ПОКУПКА EURO")
    run_and_show(["python", "main.py", "buy",
                  "--currency", "EUR",
                  "--amount", "200"], 1)

    print("\n9. 📈 ПРОСМОТР ПОРТФЕЛЯ")
    run_and_show(["python", "main.py", "show-portfolio"], 2)

    print("\n10. 📊 ПОЛУЧЕНИЕ КУРСА BTC/USD")
    run_and_show(["python", "main.py", "get-rate",
                  "--from", "USD",
                  "--to", "BTC"], 1)

    print("\n11. 🔄 ПРОДАЖА ЧАСТИ BITCOIN")
    run_and_show(["python", "main.py", "sell",
                  "--currency", "BTC",
                  "--amount", "0.03"], 1)

    print("\n12. 💼 ИТОГОВЫЙ ПОРТФЕЛЬ")
    run_and_show(["python", "main.py", "show-portfolio"], 2)

    print("\n13. ⚙️  КОНФИГУРАЦИЯ ПРОЕКТА")
    run_and_show(["python", "main.py", "config", "--section", "api"], 1)

    print("\n14. 🗃️  СТАТУС КЭША")
    run_and_show(["python", "main.py", "cache", "status"], 1)

    print("\n15. 👋 ВЫХОД ИЗ СИСТЕМЫ")
    run_and_show(["python", "main.py", "logout"], 1)

    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)

    # Показываем созданные файлы
    print("\n📁 СОЗДАННЫЕ ФАЙЛЫ:")
    if os.path.exists("data"):
        for file in os.listdir("data"):
            size = os.path.getsize(f"data/{file}")
            print(f"  • data/{file}: {size} байт")


if __name__ == "__main__":
    main()