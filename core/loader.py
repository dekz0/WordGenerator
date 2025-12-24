"""
Загрузчик данных из Excel.
Single Responsibility: только загрузка данных.
"""

from pathlib import Path
from typing import Protocol
import pandas as pd


class DataLoaderError(Exception):
    """Исключение при загрузке данных."""

    pass


class DataLoaderProtocol(Protocol):
    """Интерфейс загрузчика данных (Open/Closed principle)."""

    def load(self, file_path: Path) -> list[dict]: ...
    def get_columns(self, file_path: Path) -> list[str]: ...


class ExcelLoader:
    """
    Загрузчик Excel файлов.
    Преобразует данные в список словарей для дальнейшей обработки.
    """

    SUPPORTED_EXTENSIONS = (".xlsx", ".xls")

    def load(self, file_path: Path) -> list[dict]:
        """
        Загрузить данные из Excel файла.

        Args:
            file_path: Путь к Excel файлу

        Returns:
            Список словарей, где ключи - названия колонок

        Raises:
            DataLoaderError: При ошибке загрузки
        """
        self._validate_file(file_path)

        try:
            # Используем openpyxl для xlsx (быстрее)
            df = pd.read_excel(
                file_path,
                engine="openpyxl" if file_path.suffix == ".xlsx" else None,
                dtype=str,  # Все как строки для сохранения форматирования
            )

            # Убираем пробелы из названий колонок
            df.columns = df.columns.str.strip()

            # Заполняем NaN пустыми строками
            df = df.fillna("")

            # Преобразуем в список словарей
            records = df.to_dict("records")

            if not records:
                raise DataLoaderError("Excel файл пуст или не содержит данных")

            return records

        except DataLoaderError:
            raise
        except Exception as e:
            raise DataLoaderError(f"Ошибка чтения Excel файла: {e}")

    def get_columns(self, file_path: Path) -> list[str]:
        """
        Получить список колонок из Excel файла.

        Args:
            file_path: Путь к Excel файлу

        Returns:
            Список названий колонок
        """
        self._validate_file(file_path)

        try:
            df = pd.read_excel(
                file_path,
                engine="openpyxl" if file_path.suffix == ".xlsx" else None,
                nrows=0,  # Читаем только заголовки
            )
            return [col.strip() for col in df.columns.tolist()]
        except Exception as e:
            raise DataLoaderError(f"Ошибка чтения заголовков Excel: {e}")

    def _validate_file(self, file_path: Path) -> None:
        """Проверить корректность файла."""
        if not file_path.exists():
            raise DataLoaderError(f"Файл не найден: {file_path}")

        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise DataLoaderError(
                f"Неподдерживаемый формат файла: {file_path.suffix}. "
                f"Поддерживаются: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )
