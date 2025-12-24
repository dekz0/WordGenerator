"""
Работа с Word шаблонами.
Single Responsibility: извлечение переменных и рендеринг шаблона.
"""

from pathlib import Path
from typing import Protocol

from docxtpl import DocxTemplate


class TemplateError(Exception):
    """Исключение при работе с шаблоном."""

    pass


class TemplateEngineProtocol(Protocol):
    """Интерфейс движка шаблонов (Open/Closed principle)."""

    def extract_variables(self) -> set[str]: ...
    def render(self, context: dict) -> bytes: ...


class WordTemplate:
    """
    Работа с Word шаблоном на базе docxtpl (Jinja2).
    Поддерживает переменные вида {{ переменная }}.
    """

    def __init__(self, template_path: Path):
        """
        Args:
            template_path: Путь к Word шаблону
        """
        self._template_path = template_path
        self._validate_file()
        self._variables: set[str] | None = None

    def _validate_file(self) -> None:
        """Проверить корректность файла шаблона."""
        if not self._template_path.exists():
            raise TemplateError(f"Шаблон не найден: {self._template_path}")

        if self._template_path.suffix.lower() != ".docx":
            raise TemplateError(
                f"Неподдерживаемый формат шаблона: {self._template_path.suffix}. "
                f"Поддерживается только .docx"
            )

    def extract_variables(self) -> set[str]:
        """
        Извлечь все переменные из шаблона.

        Returns:
            Множество имён переменных
        """
        if self._variables is not None:
            return self._variables

        try:
            doc = DocxTemplate(self._template_path)

            # Используем метод get_undeclared_template_variables
            self._variables = doc.get_undeclared_template_variables()

            return self._variables

        except Exception as e:
            error_msg = str(e)

            # Проверяем на типичные ошибки синтаксиса Jinja2
            if "expected token" in error_msg and "got" in error_msg:
                raise TemplateError(
                    f"Ошибка синтаксиса в шаблоне!\n\n"
                    f"Вероятно, в названии переменной есть пробел.\n"
                    f"Пример ошибки: {{{{ city district }}}} \n"
                    f"Правильно: {{{{ city_district }}}}\n\n"
                    f"Используйте подчёркивание (_) вместо пробелов в названиях переменных.\n\n"
                    f"Техническая информация: {error_msg}"
                )

            raise TemplateError(f"Ошибка извлечения переменных из шаблона: {e}")

    def render(self, context: dict) -> bytes:
        """
        Отрендерить шаблон с данными.

        Args:
            context: Словарь с данными для подстановки

        Returns:
            Байты готового документа
        """
        try:
            # Создаём новый экземпляр для каждого рендера (thread-safe)
            doc = DocxTemplate(self._template_path)
            doc.render(context)

            # Сохраняем в байты
            from io import BytesIO

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            return buffer.read()

        except Exception as e:
            raise TemplateError(f"Ошибка рендеринга шаблона: {e}")

    @property
    def path(self) -> Path:
        return self._template_path

    @property
    def variables(self) -> set[str]:
        return self.extract_variables()
