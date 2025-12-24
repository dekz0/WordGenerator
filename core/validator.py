"""
Валидатор данных и шаблонов.
Single Responsibility: только валидация.
"""

from dataclasses import dataclass
from typing import Protocol


class ValidationError(Exception):
    """Исключение валидации с понятным сообщением."""

    pass


@dataclass
class ValidationResult:
    """Результат валидации."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @classmethod
    def success(cls, warnings: list[str] | None = None) -> "ValidationResult":
        return cls(is_valid=True, errors=[], warnings=warnings or [])

    @classmethod
    def failure(
        cls, errors: list[str], warnings: list[str] | None = None
    ) -> "ValidationResult":
        return cls(is_valid=False, errors=errors, warnings=warnings or [])


class ValidatorProtocol(Protocol):
    """Интерфейс валидатора (Dependency Inversion)."""

    def validate(
        self, data: list[dict], template_vars: set[str]
    ) -> ValidationResult: ...


class DataValidator:
    """
    Валидатор данных Excel и соответствия шаблону.
    Предоставляет понятные сообщения об ошибках для пользователя.
    """

    def __init__(self, max_rows: int = 5000):
        self._max_rows = max_rows

    def validate(self, data: list[dict], template_vars: set[str]) -> ValidationResult:
        """
        Валидировать данные на соответствие шаблону.

        Args:
            data: Список словарей с данными из Excel
            template_vars: Множество переменных из шаблона

        Returns:
            Результат валидации с ошибками и предупреждениями
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Проверка на пустые данные
        if not data:
            errors.append("Excel файл не содержит данных")
            return ValidationResult.failure(errors)

        # Проверка количества строк
        if len(data) > self._max_rows:
            errors.append(
                f"Превышен лимит строк: {len(data)} > {self._max_rows}. "
                f"Разбейте файл на части."
            )
            return ValidationResult.failure(errors)

        # Получаем колонки из данных
        excel_columns = set(data[0].keys())

        # Проверяем наличие всех переменных шаблона в колонках Excel
        missing_columns = template_vars - excel_columns
        if missing_columns:
            errors.append(
                f"В Excel отсутствуют колонки для переменных шаблона: "
                f"{', '.join(sorted(missing_columns))}"
            )

        # Предупреждение о неиспользуемых колонках
        unused_columns = excel_columns - template_vars
        if unused_columns:
            warnings.append(
                f"Колонки не используются в шаблоне: "
                f"{', '.join(sorted(unused_columns))}"
            )

        # Проверка на пустые значения в используемых колонках
        empty_cells = self._find_empty_cells(data, template_vars)
        if empty_cells:
            warnings.append(
                f"Найдены пустые значения в строках: "
                f"{', '.join(map(str, empty_cells[:10]))}"
                + (f" и ещё {len(empty_cells) - 10}" if len(empty_cells) > 10 else "")
            )

        if errors:
            return ValidationResult.failure(errors, warnings)

        return ValidationResult.success(warnings)

    def validate_row(self, row: dict, template_vars: set[str]) -> list[str]:
        """
        Валидировать отдельную строку данных.

        Args:
            row: Словарь с данными строки
            template_vars: Множество переменных из шаблона

        Returns:
            Список ошибок (пустой если всё ок)
        """
        errors = []

        for var in template_vars:
            if var not in row:
                errors.append(f"Отсутствует значение для переменной: {var}")

        return errors

    def _find_empty_cells(self, data: list[dict], columns: set[str]) -> list[int]:
        """Найти строки с пустыми значениями в указанных колонках."""
        empty_rows = []

        for idx, row in enumerate(
            data, start=2
        ):  # +2 т.к. Excel начинается с 1 + заголовок
            for col in columns:
                if col in row and (row[col] is None or str(row[col]).strip() == ""):
                    empty_rows.append(idx)
                    break

        return empty_rows
