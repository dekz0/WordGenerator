"""
Экспортер документов.
Single Responsibility: сохранение файлов и управление директориями.
"""

from pathlib import Path
from typing import Protocol
import re


class ExporterError(Exception):
    """Исключение при экспорте."""

    pass


class ExporterProtocol(Protocol):
    """Интерфейс экспортера (Open/Closed principle)."""

    def save(self, content: bytes, filename: str) -> Path: ...
    def generate_filename(self, pattern: str, context: dict, index: int) -> str: ...


class DocumentExporter:
    """
    Экспортер готовых документов.
    Создаёт папки, формирует имена файлов, сохраняет документы.
    """

    # Недопустимые символы в имени файла
    INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: Директория для сохранения документов
        """
        self._output_dir = output_dir
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Создать директорию если не существует."""
        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ExporterError(f"Не удалось создать папку для результатов: {e}")

    def save(self, content: bytes, filename: str) -> Path:
        """
        Сохранить документ.

        Args:
            content: Содержимое документа в байтах
            filename: Имя файла

        Returns:
            Путь к сохранённому файлу
        """
        # Очищаем имя файла от недопустимых символов
        safe_filename = self._sanitize_filename(filename)

        # Добавляем расширение если нет
        if not safe_filename.endswith(".docx"):
            safe_filename += ".docx"

        file_path = self._output_dir / safe_filename

        # Если файл существует - добавляем номер
        file_path = self._get_unique_path(file_path)

        try:
            file_path.write_bytes(content)
            return file_path
        except Exception as e:
            raise ExporterError(f"Ошибка сохранения файла {filename}: {e}")

    def generate_filename(self, pattern: str, context: dict, index: int) -> str:
        """
        Сгенерировать имя файла по паттерну.

        Args:
            pattern: Паттерн имени (например, "Договор_{ФИО}_{index}")
            context: Словарь с данными для подстановки
            index: Индекс строки

        Returns:
            Имя файла
        """
        # Добавляем index в контекст
        full_context = {**context, "index": str(index)}

        filename = pattern

        # Заменяем {переменная} на значения
        for key, value in full_context.items():
            placeholder = "{" + key + "}"
            if placeholder in filename:
                filename = filename.replace(placeholder, str(value))

        return self._sanitize_filename(filename)

    def _sanitize_filename(self, filename: str) -> str:
        """Очистить имя файла от недопустимых символов."""
        # Заменяем недопустимые символы на подчёркивание
        sanitized = self.INVALID_CHARS_PATTERN.sub("_", filename)

        # Убираем множественные подчёркивания
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")

        # Убираем подчёркивания по краям
        sanitized = sanitized.strip("_")

        # Ограничиваем длину (255 - длина расширения)
        max_length = 250
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized or "document"

    def _get_unique_path(self, file_path: Path) -> Path:
        """Получить уникальный путь если файл уже существует."""
        if not file_path.exists():
            return file_path

        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1

        while file_path.exists():
            file_path = file_path.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        return file_path

    @property
    def output_dir(self) -> Path:
        return self._output_dir
