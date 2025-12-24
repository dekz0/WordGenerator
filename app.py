"""
Точка входа в приложение.
Связывает UI с бизнес-логикой.
"""

import os
import sys
from pathlib import Path
from threading import Thread

# Подавляем предупреждение macOS о NSOpenPanel
os.environ["TK_SILENCE_DEPRECATION"] = "1"

# Добавляем корневую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from core.generator import DocumentGenerator, GeneratorError
from services.logger import get_logger
from services.progress import ProgressInfo
from ui.main_window import MainWindow


class Application:
    """
    Главный класс приложения.
    Связывает UI с core слоем (Mediator pattern).
    """

    def __init__(self):
        # Инициализация логгера
        self._logger = get_logger(settings.log_file)
        self._logger.info("=" * 50)
        self._logger.info("Запуск приложения")

        # Инициализация генератора
        self._generator = DocumentGenerator(
            max_workers=settings.MAX_WORKERS,
            filename_pattern=settings.FILENAME_PATTERN,
            logger=self._logger,
        )

        # Инициализация UI
        self._window = MainWindow(
            title=settings.WINDOW_TITLE,
            size=settings.WINDOW_SIZE,
            default_output_dir=settings.output_dir,
        )

        # Привязка callbacks
        self._window.set_on_generate(self._on_generate)
        self._window.set_on_cancel(self._on_cancel)

        # Текущий поток генерации
        self._generation_thread: Thread | None = None

    def _on_generate(
        self, excel_path: Path, template_path: Path, output_dir: Path
    ) -> None:
        """
        Callback генерации документов.
        Запускается в отдельном потоке чтобы не блокировать UI.
        """

        def generate_task():
            try:
                result = self._generator.generate(
                    excel_path=excel_path,
                    template_path=template_path,
                    output_dir=output_dir,
                    progress_callback=self._on_progress,
                )

                # Показываем результат в UI потоке
                self._window.after(
                    0,
                    lambda r=result: self._window.show_result(
                        success=r.is_complete or r.success_count > 0,
                        message=r.summary,
                        output_dir=r.output_dir,
                    ),
                )

            except GeneratorError as err:
                error_msg = str(err)
                self._window.after(
                    0, lambda msg=error_msg: self._window.show_error(msg)
                )
            except Exception as err:
                error_msg = f"Произошла ошибка: {err}"
                self._logger.error(f"Непредвиденная ошибка: {err}")
                self._window.after(
                    0, lambda msg=error_msg: self._window.show_error(msg)
                )

        # Запускаем в отдельном потоке
        self._generation_thread = Thread(target=generate_task, daemon=True)
        self._generation_thread.start()

    def _on_cancel(self) -> None:
        """Callback отмены генерации."""
        self._generator.cancel()
        self._window.reset()

    def _on_progress(self, progress: ProgressInfo) -> None:
        """Callback обновления прогресса."""
        self._window.update_progress(progress)

    def run(self) -> None:
        """Запустить приложение."""
        self._logger.info("UI инициализирован, запуск главного цикла")
        self._window.mainloop()
        self._logger.info("Приложение завершено")


def main():
    """Главная функция."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
