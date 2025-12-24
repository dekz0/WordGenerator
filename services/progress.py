"""
Сервис отслеживания прогресса.
Single Responsibility: только управление прогрессом.
"""

from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass
class ProgressInfo:
    """Информация о прогрессе."""

    current: int
    total: int
    message: str = ""

    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100


class ProgressCallback(Protocol):
    """Интерфейс callback-а прогресса (Dependency Inversion)."""

    def __call__(self, progress: ProgressInfo) -> None: ...


class ProgressTracker:
    """
    Трекер прогресса выполнения.
    UI подписывается на обновления через callback.
    """

    def __init__(self, callback: Callable[[ProgressInfo], None] | None = None):
        self._callback = callback
        self._current = 0
        self._total = 0

    def set_total(self, total: int) -> None:
        """Установить общее количество шагов."""
        self._total = total
        self._current = 0
        self._notify("Начало обработки...")

    def update(self, message: str = "") -> None:
        """Увеличить прогресс на 1."""
        self._current += 1
        self._notify(message)

    def set_progress(self, current: int, message: str = "") -> None:
        """Установить конкретное значение прогресса."""
        self._current = current
        self._notify(message)

    def complete(self, message: str = "Завершено") -> None:
        """Отметить завершение."""
        self._current = self._total
        self._notify(message)

    def _notify(self, message: str) -> None:
        """Уведомить подписчика о прогрессе."""
        if self._callback:
            info = ProgressInfo(
                current=self._current, total=self._total, message=message
            )
            self._callback(info)

    @property
    def current(self) -> int:
        return self._current

    @property
    def total(self) -> int:
        return self._total
