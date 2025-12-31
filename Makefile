install:
	poetry install

project:
	@echo "Usage:"
	@echo "  make register USERNAME=alice PASSWORD=1234"
	@echo "  make login USERNAME=alice PASSWORD=1234"
	@echo "  make portfolio"
	@echo "  Or use directly: poetry run project <command>"

register:
	poetry run project register --username $(USERNAME) --password $(PASSWORD)

login:
	poetry run project login --username $(USERNAME) --password $(PASSWORD)

portfolio:
	poetry run project show-portfolio

buy:
	poetry run project buy --currency $(CURRENCY) --amount $(AMOUNT)

sell:
	poetry run project sell --currency $(CURRENCY) --amount $(AMOUNT)

get-rate:
	poetry run project get-rate --from $(FROM) --to $(TO)

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