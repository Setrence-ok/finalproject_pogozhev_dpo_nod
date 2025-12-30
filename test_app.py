import subprocess
import json
import os


def test_workflow():
    """Тестовый рабочий процесс"""

    # Очистка данных (для тестов)
    if os.path.exists("data"):
        for file in os.listdir("data"):
            if file.endswith(".json"):
                os.remove(f"data/{file}")

    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ВАЛЮТНОГО КОШЕЛЬКА")
    print("=" * 60)

    # Команды для выполнения
    commands = [
        # Регистрация пользователя
        "python main.py register --username alice, --password 123456",

        # Вход
        "python main.py login --username alice, --password 123456",

        # Просмотр пустого портфеля
        "python main.py show-portfolio",

        # Покупка BTC
        "python main.py buy --currency BTC --amount 0.05",

        # Покупка EUR
        "python main.py buy --currency EUR --amount 200",

        # Просмотр портфеля
        "python main.py show-portfolio",

        # Получение курса
        "python main.py get-rate --from USD --to BTC",

        # Продажа части BTC
        "python main.py sell --currency BTC --amount 0.01",

        # Финальный просмотр портфеля
        "python main.py show-portfolio",

        # Выход
        "python main.py logout",
    ]

    # Выполнение команд
    for cmd in commands:
        print(f"\n>>> {cmd}")
        subprocess.run(cmd, shell=True)


def test_login_fix():
    """Тестирование исправления логина"""
    print("\n" + "=" * 60)
    print("Тестирование исправления проблемы с логином")
    print("=" * 60)

    # Очищаем данные
    import shutil
    if os.path.exists("data"):
        shutil.rmtree("data")
    os.makedirs("data", exist_ok=True)

    # Тестовые команды
    commands = [
        # Регистрация
        ["python", "main.py", "register", "--username", "fixeduser", "--password", "123456"],
        # Логин (должен работать)
        ["python", "main.py", "login", "--username", "fixeduser", "--password", "123456"],
        # Неправильный пароль
        ["python", "main.py", "login", "--username", "fixeduser", "--password", "wrong"],
    ]

    for cmd in commands:
        print(f"\n>>> {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout[:200])
        if result.stderr and "ERROR" in result.stderr:
            print("STDERR:", result.stderr[:100])

        if "Неверный пароль" in result.stdout or "InvalidPasswordError" in str(result.stderr):
            print("✅ Правильная обработка неверного пароля")


if __name__ == "__main__":
    test_login_fix()
    test_workflow()