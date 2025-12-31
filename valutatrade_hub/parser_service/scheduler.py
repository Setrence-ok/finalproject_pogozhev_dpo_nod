import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional

from .updater import RatesUpdater
from .config import ParserConfig


class RatesScheduler:
    """Планировщик для периодического обновления курсов"""

    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
        self.updater = RatesUpdater(self.config)
        self.logger = logging.getLogger('valutatrade.scheduler')
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self, interval_minutes: int = 5):
        """
        Запустить планировщик в фоновом режиме

        Args:
            interval_minutes: интервал обновления в минутах (по умолчанию 5)
        """
        if self._thread and self._thread.is_alive():
            self.logger.warning("Планировщик уже запущен")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_scheduler,
            args=(interval_minutes,),
            daemon=True,
            name="RatesScheduler"
        )
        self._thread.start()
        self.logger.info(f"Планировщик запущен с интервалом {interval_minutes} минут")

    def stop(self):
        """Остановить планировщик"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self.logger.info("Планировщик остановлен")

    def _run_scheduler(self, interval_minutes: int):
        """Основной цикл планировщика"""
        interval_seconds = interval_minutes * 60

        while not self._stop_event.is_set():
            try:
                self.logger.info("Запуск запланированного обновления курсов...")

                # Запускаем обновление
                updated_count = self.updater.run_update()

                if updated_count > 0:
                    self.logger.info(f"Обновлено {updated_count} курсов")
                else:
                    self.logger.warning("Не удалось обновить курсы")

                # Рассчитываем время следующего обновления
                next_update = datetime.now() + timedelta(minutes=interval_minutes)
                self.logger.info(f"Следующее обновление в {next_update.strftime('%H:%M:%S')}")

            except Exception as e:
                self.logger.error(f"Ошибка в планировщике: {e}")

            # Ожидаем до следующего обновления или команды остановки
            for _ in range(interval_seconds * 10):  # Проверяем каждые 0.1 секунду
                if self._stop_event.wait(timeout=0.1):
                    break

    def run_once(self):
        """Запустить одно обновление (синхронно)"""
        try:
            self.logger.info("Запуск разового обновления курсов...")
            updated_count = self.updater.run_update()

            if updated_count > 0:
                self.logger.info(f"Обновлено {updated_count} курсов")
                return updated_count
            else:
                self.logger.warning("Не удалось обновить курсы")
                return 0

        except Exception as e:
            self.logger.error(f"Ошибка при обновлении: {e}")
            return 0

    def is_running(self) -> bool:
        """Проверить, работает ли планировщик"""
        return self._thread is not None and self._thread.is_alive()


def start_background_scheduler(interval_minutes: int = 5):
    """
    Запустить планировщик в фоновом режиме (удобная функция)

    Args:
        interval_minutes: интервал обновления в минутах
    """
    scheduler = RatesScheduler()
    scheduler.start(interval_minutes)
    return scheduler