"""
Централизованные настройки приложения.
Следуя принципу Single Responsibility - только конфигурация.
"""

from dataclasses import dataclass
from pathlib import Path
import sys


def get_app_dir() -> Path:
    """Получить директорию приложения (для exe и dev режима)."""
    if getattr(sys, "frozen", False):
        # Запущено как exe
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


@dataclass(frozen=True)
class AppSettings:
    """Неизменяемые настройки приложения."""

    # Лимиты
    MAX_ROWS: int = 5000
    MAX_WORKERS: int = 4  # Потоки для параллельной обработки

    # Паттерн имени файла (можно использовать переменные из Excel)
    FILENAME_PATTERN: str = "Документ_{index}"

    # Расширения файлов
    EXCEL_EXTENSIONS: tuple = (".xlsx", ".xls")
    WORD_EXTENSIONS: tuple = (".docx",)

    # UI настройки
    WINDOW_TITLE: str = "Генератор документов"
    WINDOW_SIZE: tuple = (700, 500)

    # Пути по умолчанию
    @property
    def app_dir(self) -> Path:
        return get_app_dir()

    @property
    def output_dir(self) -> Path:
        return self.app_dir / "output"

    @property
    def log_file(self) -> Path:
        return self.app_dir / "app.log"

    @property
    def templates_dir(self) -> Path:
        return self.app_dir / "templates"


# Глобальный экземпляр настроек (Singleton через модуль)
settings = AppSettings()
