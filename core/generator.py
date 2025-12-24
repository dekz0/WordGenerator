"""
Генератор документов - главный оркестратор.
Single Responsibility: координация процесса генерации.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core.loader import ExcelLoader, DataLoaderError
from core.template import WordTemplate, TemplateError
from core.validator import DataValidator
from core.exporter import DocumentExporter
from services.logger import AppLogger, get_logger
from services.progress import ProgressTracker, ProgressInfo


class GeneratorError(Exception):
    """Исключение генератора."""

    pass


@dataclass
class GenerationResult:
    """Результат генерации документов."""

    success_count: int
    error_count: int
    total_count: int
    errors: list[str]
    output_dir: Path

    @property
    def is_complete(self) -> bool:
        return self.error_count == 0

    @property
    def summary(self) -> str:
        if self.is_complete:
            return f"✓ Успешно создано {self.success_count} документов"
        return (
            f"Создано {self.success_count} из {self.total_count} документов. "
            f"Ошибок: {self.error_count}"
        )


class DocumentGenerator:
    """
    Главный оркестратор генерации документов.
    Координирует работу loader, validator, template и exporter.
    Поддерживает многопоточную обработку для скорости.
    """

    def __init__(
        self,
        loader: ExcelLoader | None = None,
        validator: DataValidator | None = None,
        logger: AppLogger | None = None,
        max_workers: int = 4,
        filename_pattern: str = "Документ_{index}",
    ):
        """
        Args:
            loader: Загрузчик данных
            validator: Валидатор данных
            logger: Логгер
            max_workers: Количество потоков для параллельной обработки
            filename_pattern: Паттерн имени файла
        """
        self._loader = loader or ExcelLoader()
        self._validator = validator or DataValidator()
        self._logger = logger or get_logger()
        self._max_workers = max_workers
        self._filename_pattern = filename_pattern
        self._is_cancelled = False

    def generate(
        self,
        excel_path: Path,
        template_path: Path,
        output_dir: Path,
        progress_callback: Callable[[ProgressInfo], None] | None = None,
    ) -> GenerationResult:
        """
        Сгенерировать документы.

        Args:
            excel_path: Путь к Excel файлу с данными
            template_path: Путь к Word шаблону
            output_dir: Директория для сохранения результатов
            progress_callback: Callback для отслеживания прогресса

        Returns:
            Результат генерации
        """
        self._is_cancelled = False
        progress = ProgressTracker(progress_callback)
        errors: list[str] = []

        self._logger.info("Начало генерации документов")
        self._logger.info(f"Excel: {excel_path}")
        self._logger.info(f"Шаблон: {template_path}")
        self._logger.info(f"Выходная папка: {output_dir}")

        try:
            # 1. Загружаем данные из Excel
            progress.set_total(100)
            progress.set_progress(5, "Загрузка данных из Excel...")

            data = self._loader.load(excel_path)
            self._logger.info(f"Загружено {len(data)} строк из Excel")

            # 2. Загружаем шаблон и извлекаем переменные
            progress.set_progress(10, "Анализ шаблона...")

            template = WordTemplate(template_path)
            template_vars = template.extract_variables()
            self._logger.info(
                f"Найдено {len(template_vars)} переменных в шаблоне: {template_vars}"
            )

            # 3. Валидация данных
            progress.set_progress(15, "Проверка данных...")

            validation = self._validator.validate(data, template_vars)

            if not validation.is_valid:
                for error in validation.errors:
                    self._logger.error(error)
                raise GeneratorError("\n".join(validation.errors))

            for warning in validation.warnings:
                self._logger.warning(warning)

            # 4. Создаём экспортер
            exporter = DocumentExporter(output_dir)

            # 5. Генерируем документы с многопоточностью
            progress.set_progress(20, "Генерация документов...")

            total = len(data)
            success_count = 0
            error_count = 0

            # Используем ThreadPoolExecutor для параллельной обработки
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = {}

                for idx, row in enumerate(data, start=1):
                    if self._is_cancelled:
                        break

                    future = executor.submit(
                        self._process_row, template_path, row, idx, exporter
                    )
                    futures[future] = idx

                for future in as_completed(futures):
                    if self._is_cancelled:
                        break

                    idx = futures[future]

                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        error_msg = f"Строка {idx}: {str(e)}"
                        errors.append(error_msg)
                        self._logger.error(error_msg)
                        error_count += 1

                    # Обновляем прогресс (от 20% до 100%)
                    processed = success_count + error_count
                    percent = 20 + int((processed / total) * 80)
                    progress.set_progress(
                        percent, f"Обработано {processed} из {total}..."
                    )

            progress.complete(f"Готово! Создано {success_count} документов")

            self._logger.info(
                f"Генерация завершена. Успешно: {success_count}, Ошибок: {error_count}"
            )

            return GenerationResult(
                success_count=success_count,
                error_count=error_count,
                total_count=total,
                errors=errors,
                output_dir=output_dir,
            )

        except DataLoaderError as e:
            self._logger.error(f"Ошибка загрузки данных: {e}")
            raise GeneratorError(str(e))
        except TemplateError as e:
            self._logger.error(f"Ошибка шаблона: {e}")
            raise GeneratorError(str(e))
        except GeneratorError:
            raise
        except Exception as e:
            self._logger.error(f"Непредвиденная ошибка: {e}")
            raise GeneratorError(f"Непредвиденная ошибка: {e}")

    def _process_row(
        self, template_path: Path, row: dict, index: int, exporter: DocumentExporter
    ) -> bool:
        """
        Обработать одну строку данных.

        Args:
            template_path: Путь к шаблону
            row: Данные строки
            index: Индекс строки
            exporter: Экспортер

        Returns:
            True если успешно, False при ошибке
        """
        try:
            # Создаём новый экземпляр шаблона для thread-safety
            template = WordTemplate(template_path)

            # Рендерим документ
            content = template.render(row)

            # Генерируем имя файла
            filename = exporter.generate_filename(self._filename_pattern, row, index)

            # Сохраняем
            exporter.save(content, filename)

            return True

        except Exception as e:
            self._logger.error(f"Ошибка обработки строки {index}: {e}")
            return False

    def cancel(self) -> None:
        """Отменить генерацию."""
        self._is_cancelled = True
        self._logger.info("Генерация отменена пользователем")

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled
