.PHONY: install project build publish package-install lint test clean parser-test \
        shell start run help init format debug-login setup-api

# Установка зависимостей
install:
	poetry install

# Запуск основного приложения (одна команда)
project:
	poetry run python main.py $(filter-out $@,$(MAKECMDGOALS))

# Запуск парсера отдельно
parser:
	poetry run python -m valutatrade_hub.parser_service.cli $(filter-out $@,$(MAKECMDGOALS))

# Сборка пакета
build:
	poetry build

# Публикация (тестовый режим)
publish:
	poetry publish --dry-run

# Установка пакета локально
package-install:
	python3 -m pip install dist/*.whl

# Проверка стиля кода
lint:
	poetry run ruff check .
	poetry run ruff format --check .

# Форматирование кода
format:
	poetry run ruff format .

# Тестирование
test:
	poetry run pytest tests/ -v

# Тестирование парсера
parser-test:
	poetry run python test_parser.py

# Тестирование всего приложения
test-all:
	poetry run python test_app.py

# Очистка временных файлов
clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -f *.log
	rm -rf logs/*.log
	rm -rf data/*.json data/*.tmp
	rm -rf dist/ build/ *.egg-info/

# Запуск полного тестового сценария
demo:
	@echo "🚀 Запуск демонстрационного сценария..."
	poetry run python test_app.py
	@echo "\n⏳ Ожидание 3 секунды..."
	sleep 3
	poetry run python test_parser.py

# Инициализация проекта
init:
	mkdir -p data logs
	cp config.example.json config.json 2>/dev/null || echo "Создайте config.json вручную"
	@echo "✅ Проект инициализирован"

# Настройка API ключа
setup-api:
	@echo "🔑 Настройка API ключей для парсера"
	@echo "=" * 60
	@echo "1. ExchangeRate-API (фиатные валюты):"
	@echo "   Получите бесплатный ключ на https://www.exchangerate-api.com/"
	@echo "   Затем выполните:"
	@echo "   export EXCHANGERATE_API_KEY='ваш_ключ_здесь'"
	@echo ""
	@echo "2. CoinGecko (криптовалюты):"
	@echo "   Работает без ключа (с ограничениями)"
	@echo ""
	@echo "3. Проверить текущие настройки:"
	@echo "   make project config --section api"
	@echo "=" * 60


# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make install        - Установить зависимости"
	@echo "  make project <cmd>  - Запустить команду приложения"
	@echo "  make parser <cmd>   - Запустить команду парсера"
	@echo "  make lint           - Проверить стиль кода"
	@echo "  make format         - Отформатировать код"
	@echo "  make test-all       - Запустить все тесты"
	@echo "  make demo           - Запустить демо-сценарий"
	@echo "  make clean          - Очистить временные файлы"
	@echo "  make init           - Инициализировать проект"
	@echo "  make debug-login    - Отладка системы логина"
	@echo "  make setup-api      - Инструкция по настройке API"
	@echo "  make test-data      - Создать тестовые данные"
	@echo ""
	@echo "Примеры:"
	@echo "  make project login --username demo --password demo"
	@echo "  make project show-rates --top 3"
	@echo "  make parser update --source coingecko"
	@echo "  make parser info --check-api"