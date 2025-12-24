"""
Сервис логирования.
Single Responsibility: только логирование событий.
"""

import logging
from pathlib import Path
from typing import Protocol


class LoggerProtocol(Protocol):
    """Интерфейс логгера (Dependency Inversion)."""

    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...


class AppLogger:
    """Реализация логгера приложения."""

    _instance = None

    def __new__(cls, log_file: Path | None = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file: Path | None = None):
        if self._initialized:
            return

        self._logger = logging.getLogger("WordGenerator")
        self._logger.setLevel(logging.DEBUG)

        # Формат логов
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Консольный вывод
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # Файловый вывод
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        self._initialized = True

    def info(self, message: str) -> None:
        self._logger.info(message)

    def warning(self, message: str) -> None:
        self._logger.warning(message)

    def error(self, message: str) -> None:
        self._logger.error(message)

    def debug(self, message: str) -> None:
        self._logger.debug(message)


def get_logger(log_file: Path | None = None) -> AppLogger:
    """Фабричная функция для получения логгера."""
    return AppLogger(log_file)
