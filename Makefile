install:
	poetry install

project:
	@echo "Usage:"
	@echo "  make register"
	@echo "  make login"
	@echo "  make portfolio"
	@echo "  make buy"
	@echo "  make sell"
	@echo "  make get-rate"
	@echo "  make update-rates"
	@echo "  make show-rates"

register:
	@read -p "Username: " username; \
	read -p "Password: " password; \
	poetry run project register --username $$username --password $$password

login:
	@read -p "Username: " username; \
	read -p "Password: " password; \
	poetry run project login --username $$username --password $$password

portfolio:
	poetry run project show-portfolio

buy:
	@read -p "Currency code (BTC, ETH, USD, etc.): " currency; \
	read -p "Amount: " amount; \
	poetry run project buy --currency $$currency --amount $$amount

sell:
	@read -p "Currency code (BTC, ETH, USD, etc.): " currency; \
	read -p "Amount: " amount; \
	poetry run project sell --currency $$currency --amount $$amount

get-rate:
	@read -p "From currency (USD, etc.): " from_currency; \
	read -p "To currency (BTC, ETH, USD, etc.): " to_currency; \
	poetry run project get-rate --from "$$from_currency" --to "$$to_currency"

update-rates:
	poetry run project update-rates

show-rates:
	poetry run project show-rates

build:
	poetry build

publish:
	poetry publish --dry-run

package-install:
	python3 -m pip install dist/*.whl

lint:
	poetry run ruff check .

test:
	python test_session.py