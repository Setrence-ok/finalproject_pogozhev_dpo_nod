from ..logging_config import get_logger

logger = get_logger("usecases")

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

from .models import User, Portfolio, Wallet
from .currencies import CurrencyRegistry, Currency
from .exceptions import (
    InsufficientFundsError, CurrencyNotFoundError, ApiRequestError,
    UserNotFoundError, InvalidPasswordError, WalletNotFoundError,
    InvalidAmountError, AuthenticationError
)
from ..infra.database import db
from ..infra.settings import settings
from ..decorators import log_action, measure_time, retry_on_failure
from ..logging_config import get_logger

logger = get_logger("usecases")


class UserManager:
    """Менеджер пользователей"""

    def __init__(self):
        self.current_user: Optional[User] = None
        self.logger = logging.getLogger("usecases.UserManager")

    @log_action("REGISTER", verbose=True)
    def register(self, username: str, password: str) -> User:
        """Регистрация нового пользователя"""
        # Проверка уникальности username
        existing_user = db.get_user_by_username(username)
        if existing_user:
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        # Проверка пароля
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        # Генерация user_id
        users = db.get_all_users()
        user_id = max([u.get("user_id", 0) for u in users], default=0) + 1

        # Создание пользователя
        user = User(user_id=user_id, username=username, password=password)

        # Сохранение пользователя
        db.save_user(user.to_dict())

        # Создание пустого портфеля
        portfolio = Portfolio(user_id=user_id)
        db.save_portfolio(user_id, portfolio.to_dict())

        self.logger.info(f"User {username} registered successfully", extra={"user_id": user_id})
        return user

    @log_action("LOGIN")
    def login(self, username: str, password: str) -> User:
        """Вход пользователя с улучшенной диагностикой"""
        self.logger.debug(f"Login attempt for user: {username}")

        # Поиск пользователя
        user_data = db.get_user_by_username(username)
        if not user_data:
            self.logger.warning(f"User not found: {username}")
            raise UserNotFoundError(username)

        self.logger.debug(f"User found in DB: {user_data.get('username')}")

        try:
            # Создание объекта User с правильной загрузкой хеша
            user = User.from_dict(user_data)
            self.logger.debug(f"User object created from dict")

            # Проверка пароля с диагностикой
            if not user.verify_password(password):
                self.logger.warning(f"Invalid password for user: {username}")
                raise InvalidPasswordError()

            self.current_user = user
            self.logger.info(f"User {username} logged in successfully", extra={"user_id": user.user_id})
            return user

        except Exception as e:
            self.logger.error(f"Login error for {username}: {str(e)}", exc_info=True)
            raise

    @log_action("LOGOUT")
    def logout(self) -> None:
        """Выход пользователя"""
        if self.current_user:
            self.logger.info(f"User {self.current_user.username} logged out")
        self.current_user = None

    def get_current_portfolio(self) -> Portfolio:
        """Получение портфеля текущего пользователя"""
        if not self.current_user:
            raise AuthenticationError()

        portfolio_data = db.get_portfolio(self.current_user.user_id)

        if portfolio_data:
            return Portfolio.from_dict(portfolio_data)
        else:
            # Создание пустого портфеля, если не существует
            portfolio = Portfolio(user_id=self.current_user.user_id)
            db.save_portfolio(self.current_user.user_id, portfolio.to_dict())
            return portfolio

    def is_authenticated(self) -> bool:
        """Проверка аутентификации пользователя"""
        return self.current_user is not None


class PortfolioManager:
    """Менеджер портфелей и операций"""

    def __init__(self, user_manager: UserManager):
        self.user_manager = user_manager
        self._exchange_rates_cache = None
        self._cache_timestamp = None

    @measure_time
    def _get_exchange_rates(self, force_refresh: bool = False) -> Dict:
        """Получение курсов валют с кэшированием"""
        current_time = datetime.now()

        # Проверка необходимости обновления кэша
        if (force_refresh or
                not self._exchange_rates_cache or
                not self._cache_timestamp or
                (current_time - self._cache_timestamp).total_seconds() > settings.rates_ttl_seconds):

            # Проверка свежести данных в БД
            if not db.is_rate_fresh() or force_refresh:
                logger.info("Exchange rates cache is stale, refreshing...")
                self._refresh_exchange_rates()

            # Загрузка из БД
            rates_data = db.get_exchange_rates()
            self._exchange_rates_cache = rates_data.get("rates", {})
            self._cache_timestamp = datetime.fromisoformat(rates_data["last_refresh"])

        return self._exchange_rates_cache

    @retry_on_failure(max_retries=3, delay=2.0)
    def _refresh_exchange_rates(self) -> None:
        """Обновление курсов валют из внешнего источника"""
        # В реальном проекте здесь был бы запрос к API
        # Для демонстрации имитируем API запрос

        logger.info("Refreshing exchange rates from external API")

        # Имитация случайной ошибки API (для демонстрации retry)
        import random
        if random.random() < 0.3:  # 30% шанс ошибки
            raise ApiRequestError("API временно недоступен")

        # Обновление данных в БД
        db._refresh_exchange_rates()
        logger.info("Exchange rates refreshed successfully")

    @log_action("SHOW_PORTFOLIO", verbose=True)
    def show_portfolio(self, base_currency: str = "USD") -> Tuple[Dict, float]:
        """Показать портфель пользователя"""
        if not self.user_manager.current_user:
            raise AuthenticationError()

        # Проверка валидности базовой валюты
        try:
            CurrencyRegistry.get_currency(base_currency)
        except CurrencyNotFoundError:
            raise CurrencyNotFoundError(base_currency)

        portfolio = self.user_manager.get_current_portfolio()
        if not portfolio:
            return {}, 0.0

        # Получение текущих курсов
        exchange_rates = self._get_exchange_rates()

        # Получение информации о кошельках
        wallets_info = {}
        total_value = 0.0

        for currency_code, wallet in portfolio.wallets.items():
            try:
                # Проверка валидности валюты
                CurrencyRegistry.get_currency(currency_code)

                # Конвертация в базовую валюту
                if currency_code == base_currency:
                    value_in_base = wallet.balance
                else:
                    rate_key = f"{currency_code}_{base_currency}"
                    reverse_key = f"{base_currency}_{currency_code}"

                    if rate_key in exchange_rates:
                        rate = exchange_rates[rate_key]["rate"]
                        value_in_base = wallet.balance * rate
                    elif reverse_key in exchange_rates:
                        rate = 1 / exchange_rates[reverse_key]["rate"]
                        value_in_base = wallet.balance * rate
                    else:
                        # Конвертация через USD как промежуточную валюту
                        value_in_base = self._convert_via_usd(
                            wallet.balance, currency_code, base_currency, exchange_rates
                        )

                wallets_info[currency_code] = {
                    "balance": wallet.balance,
                    "value_in_base": value_in_base,
                    "currency_info": CurrencyRegistry.get_currency(currency_code).get_display_info()
                }

                total_value += value_in_base

            except CurrencyNotFoundError:
                logger.warning(f"Unknown currency {currency_code} in portfolio")
                continue

        return wallets_info, total_value

    def _convert_via_usd(self, amount: float, from_currency: str, to_currency: str, rates: Dict) -> float:
        """Конвертация через USD как промежуточную валюту"""
        # Конвертация from_currency -> USD
        from_to_usd_key = f"{from_currency}_USD"
        usd_to_from_key = f"USD_{from_currency}"

        if from_to_usd_key in rates:
            usd_amount = amount * rates[from_to_usd_key]["rate"]
        elif usd_to_from_key in rates:
            usd_amount = amount / rates[usd_to_from_key]["rate"]
        else:
            return 0.0  # Не можем конвертировать

        # Конвертация USD -> to_currency
        usd_to_to_key = f"USD_{to_currency}"
        to_to_usd_key = f"{to_currency}_USD"

        if usd_to_to_key in rates:
            return usd_amount * rates[usd_to_to_key]["rate"]
        elif to_to_usd_key in rates:
            return usd_amount / rates[to_to_usd_key]["rate"]
        else:
            return 0.0

    @log_action("BUY", verbose=True)
    def buy_currency(self, currency_code: str, amount: float) -> Dict:
        """Покупка валюты"""
        if not self.user_manager.current_user:
            raise AuthenticationError()

        # Валидация валюты
        try:
            currency = CurrencyRegistry.get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(currency_code)

        # Валидация суммы
        if amount <= 0:
            raise InvalidAmountError(amount)

        portfolio = self.user_manager.get_current_portfolio()

        # Получение или создание кошелька
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            wallet = portfolio.add_currency(currency_code)

        # Пополнение кошелька
        old_balance = wallet.balance
        wallet.deposit(amount)

        # Сохранение портфеля
        db.save_portfolio(self.user_manager.current_user.user_id, portfolio.to_dict())

        # Расчет стоимости покупки
        try:
            cost_in_usd = self._convert_via_usd(
                amount, currency_code, "USD", self._get_exchange_rates()
            )
        except Exception:
            cost_in_usd = 0.0

        result = {
            "currency": currency_code,
            "currency_info": currency.get_display_info(),
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": wallet.balance,
            "cost_usd": cost_in_usd,
            "user_id": self.user_manager.current_user.user_id,
            "username": self.user_manager.current_user.username,
        }

        logger.info(f"User {self.user_manager.current_user.username} bought {amount} {currency_code}")
        return result

    @log_action("SELL", verbose=True)
    def sell_currency(self, currency_code: str, amount: float) -> Dict:
        """Продажа валюты"""
        if not self.user_manager.current_user:
            raise AuthenticationError()

        # Валидация валюты
        try:
            currency = CurrencyRegistry.get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(currency_code)

        # Валидация суммы
        if amount <= 0:
            raise InvalidAmountError(amount)

        portfolio = self.user_manager.get_current_portfolio()

        # Получение кошелька
        wallet = portfolio.get_wallet(currency_code)
        if not wallet:
            raise WalletNotFoundError(currency_code)

        # Проверка достаточности средств
        if amount > wallet.balance:
            raise InsufficientFundsError(
                currency_code=currency_code,
                available=wallet.balance,
                required=amount
            )

        # Снятие средств
        old_balance = wallet.balance
        wallet.withdraw(amount)

        # Сохранение портфеля
        db.save_portfolio(self.user_manager.current_user.user_id, portfolio.to_dict())

        # Расчет выручки
        try:
            revenue_in_usd = self._convert_via_usd(
                amount, currency_code, "USD", self._get_exchange_rates()
            )
        except Exception:
            revenue_in_usd = 0.0

        result = {
            "currency": currency_code,
            "currency_info": currency.get_display_info(),
            "amount": amount,
            "old_balance": old_balance,
            "new_balance": wallet.balance,
            "revenue_usd": revenue_in_usd,
            "user_id": self.user_manager.current_user.user_id,
            "username": self.user_manager.current_user.username,
        }

        logger.info(f"User {self.user_manager.current_user.username} sold {amount} {currency_code}")
        return result

    @log_action("GET_RATE")
    @retry_on_failure(max_retries=2, delay=1.0)
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict:
        """Получение курса валюты"""
        # Валидация валют
        try:
            from_curr = CurrencyRegistry.get_currency(from_currency)
            to_curr = CurrencyRegistry.get_currency(to_currency)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(str(e).split("'")[1])

        # Получение курсов
        exchange_rates = self._get_exchange_rates()

        # Прямой курс
        rate_key = f"{from_currency}_{to_currency}"
        reverse_key = f"{to_currency}_{from_currency}"

        rate = None
        updated_at = None
        source = "cache"

        if rate_key in exchange_rates:
            rate_data = exchange_rates[rate_key]
            rate = rate_data["rate"]
            updated_at = rate_data["updated_at"]
        elif reverse_key in exchange_rates:
            rate_data = exchange_rates[reverse_key]
            rate = 1 / rate_data["rate"]
            updated_at = rate_data["updated_at"]
        else:
            # Попытка получить курс через USD
            usd_rate_from = self._get_rate_via_usd(from_currency, exchange_rates)
            usd_rate_to = self._get_rate_via_usd(to_currency, exchange_rates)

            if usd_rate_from and usd_rate_to:
                rate = usd_rate_to / usd_rate_from
                updated_at = datetime.now().isoformat()
                source = "calculated_via_USD"

        if rate is None:
            # Если курс не найден в кэше, пытаемся обновить
            logger.info(f"Rate {from_currency}-{to_currency} not found in cache, refreshing...")
            try:
                self._refresh_exchange_rates()
                exchange_rates = self._get_exchange_rates(force_refresh=True)

                if rate_key in exchange_rates:
                    rate_data = exchange_rates[rate_key]
                    rate = rate_data["rate"]
                    updated_at = rate_data["updated_at"]
                    source = "api_refresh"
                else:
                    raise ApiRequestError(f"Курс {from_currency}-{to_currency} недоступен")
            except Exception as e:
                raise ApiRequestError(f"Не удалось получить курс: {str(e)}")

        result = {
            "from": from_currency,
            "from_info": from_curr.get_display_info(),
            "to": to_currency,
            "to_info": to_curr.get_display_info(),
            "rate": rate,
            "reverse_rate": 1 / rate if rate != 0 else 0,
            "updated_at": updated_at,
            "source": source,
        }

        return result

    def _get_rate_via_usd(self, currency: str, rates: Dict) -> Optional[float]:
        """Получение курса валюты к USD"""
        if currency == "USD":
            return 1.0

        direct_key = f"{currency}_USD"
        reverse_key = f"USD_{currency}"

        if direct_key in rates:
            return rates[direct_key]["rate"]
        elif reverse_key in rates:
            return 1 / rates[reverse_key]["rate"]

        return None

    def get_supported_currencies(self, currency_type: str = "all") -> Dict[str, str]:
        """Получение списка поддерживаемых валют"""
        currencies = CurrencyRegistry.list_currencies(currency_type)
        return {code: curr.get_display_info() for code, curr in currencies.items()}