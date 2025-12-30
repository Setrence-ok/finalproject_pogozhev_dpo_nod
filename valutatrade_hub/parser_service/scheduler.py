import threading
import time
import schedule
import logging
from typing import Optional, Callable
from datetime import datetime

from .updater import updater
from .config import config

logger = logging.getLogger("parser.scheduler")


class RatesScheduler:
    """
    Планировщик для периодического обновления курсов.
    Использует библиотеку schedule для cron-like планирования.
    """

    def __init__(self, interval_minutes: int = None):
        """
        Инициализация планировщика.

        Args:
            interval_minutes: Интервал обновления в минутах
        """
        self.interval = interval_minutes or config.SCHEDULER_INTERVAL_MINUTES
        self.scheduler = schedule  # ИСПРАВЛЕНИЕ: используем модуль напрямую
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.callback: Optional[Callable] = None

        logger.info(f"Scheduler initialized with {self.interval}-minute interval")

    def start(self, background: bool = True) -> None:
        """
        Запуск планировщика.

        Args:
            background: Если True, запускает в отдельном потоке
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True

        if background:
            self.thread = threading.Thread(
                target=self._run_scheduler,
                name="RatesScheduler",
                daemon=True
            )
            self.thread.start()
            logger.info(f"Scheduler started in background thread (every {self.interval} minutes)")
        else:
            logger.info(f"Scheduler started in foreground (every {self.interval} minutes)")
            self._run_scheduler()

    def stop(self) -> None:
        """Остановка планировщика"""
        self.running = False
        schedule.clear()  # Очищаем все задания

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        logger.info("Scheduler stopped")

    def set_callback(self, callback: Callable) -> None:
        """
        Установка callback-функции, которая будет вызываться после каждого обновления.

        Args:
            callback: Функция, принимающая результат обновления
        """
        self.callback = callback
        logger.info("Callback function set for scheduler")

    def _run_scheduler(self) -> None:
        """Основной цикл планировщика"""
        logger.info("Scheduler loop started")

        # Создаем задание с указанным интервалом
        schedule.every(self.interval).minutes.do(self._scheduled_update)

        # Выполняем начальное обновление
        self._scheduled_update()

        # Основной цикл
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Проверяем каждую секунду
            except KeyboardInterrupt:
                logger.info("Scheduler interrupted by keyboard")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Ждем минуту при ошибке

        logger.info("Scheduler loop stopped")

    def _scheduled_update(self) -> None:
        """Выполнение запланированного обновления"""
        logger.info(f"Executing scheduled update at {datetime.now()}")

        try:
            result = updater.update_if_stale()

            # Вызываем callback, если установлен
            if self.callback and callable(self.callback):
                self.callback(result)

            logger.info(f"Scheduled update completed: {result.get('total_rates', 0)} rates")

        except Exception as e:
            logger.error(f"Scheduled update failed: {e}")

    def run_once(self):
        """
        Запуск одного обновления вне расписания.

        Returns:
            Результат обновления
        """
        logger.info("Running one-time update")
        return updater.run_update()

    def get_next_run(self) -> Optional[datetime]:
        """
        Получение времени следующего запланированного обновления.

        Returns:
            Время следующего запуска или None, если планировщик не запущен
        """
        if hasattr(schedule, 'next_run'):
            return schedule.next_run
        return None

    def get_status(self):
        """
        Получение статуса планировщика.

        Returns:
            Словарь со статусом
        """
        return {
            "running": self.running,
            "interval_minutes": self.interval,
            "next_run": self.get_next_run(),
            "background": self.thread is not None and self.thread.is_alive(),
        }

    def change_interval(self, interval_minutes: int) -> None:
        """
        Изменение интервала обновления.

        Args:
            interval_minutes: Новый интервал в минутах
        """
        self.interval = interval_minutes
        schedule.clear()  # Очищаем старые задания

        logger.info(f"Scheduler interval changed to {interval_minutes} minutes")


# Глобальный экземпляр планировщика
scheduler = RatesScheduler()