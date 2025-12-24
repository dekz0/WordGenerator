"""
Главное окно приложения.
Single Responsibility: только UI и взаимодействие с пользователем.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable

from services.progress import ProgressInfo


class FileSelector(ctk.CTkFrame):
    """Компонент выбора файла."""

    def __init__(self, master, label: str, filetypes: list[tuple[str, str]], **kwargs):
        super().__init__(master, **kwargs)

        self._filetypes = filetypes
        self._file_path: Path | None = None

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)

        # Label
        self._label = ctk.CTkLabel(
            self, text=label, font=ctk.CTkFont(size=14, weight="bold")
        )
        self._label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # Entry для отображения пути
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="Файл не выбран...",
            state="disabled",
            font=ctk.CTkFont(size=12),
        )
        self._entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        # Кнопка выбора
        self._button = ctk.CTkButton(
            self, text="Выбрать", width=100, command=self._select_file
        )
        self._button.grid(row=1, column=1, sticky="e")

    def _select_file(self) -> None:
        """Открыть диалог выбора файла."""
        file_path = filedialog.askopenfilename(filetypes=self._filetypes)

        if file_path:
            self._file_path = Path(file_path)
            self._entry.configure(state="normal")
            self._entry.delete(0, "end")
            self._entry.insert(0, self._file_path.name)
            self._entry.configure(state="disabled")

    @property
    def file_path(self) -> Path | None:
        return self._file_path

    def reset(self) -> None:
        """Сбросить выбор."""
        self._file_path = None
        self._entry.configure(state="normal")
        self._entry.delete(0, "end")
        self._entry.configure(state="disabled")


class FolderSelector(ctk.CTkFrame):
    """Компонент выбора папки."""

    def __init__(self, master, label: str, default_path: Path | None = None, **kwargs):
        super().__init__(master, **kwargs)

        self._folder_path: Path | None = default_path

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)

        # Label
        self._label = ctk.CTkLabel(
            self, text=label, font=ctk.CTkFont(size=14, weight="bold")
        )
        self._label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        # Entry для отображения пути
        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="Папка не выбрана...",
            state="disabled",
            font=ctk.CTkFont(size=12),
        )
        self._entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        if default_path:
            self._entry.configure(state="normal")
            self._entry.insert(0, str(default_path))
            self._entry.configure(state="disabled")

        # Кнопка выбора
        self._button = ctk.CTkButton(
            self, text="Выбрать", width=100, command=self._select_folder
        )
        self._button.grid(row=1, column=1, sticky="e")

    def _select_folder(self) -> None:
        """Открыть диалог выбора папки."""
        folder_path = filedialog.askdirectory()

        if folder_path:
            self._folder_path = Path(folder_path)
            self._entry.configure(state="normal")
            self._entry.delete(0, "end")
            self._entry.insert(0, str(self._folder_path))
            self._entry.configure(state="disabled")

    @property
    def folder_path(self) -> Path | None:
        return self._folder_path


class ProgressPanel(ctk.CTkFrame):
    """Панель прогресса."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # Статус
        self._status_label = ctk.CTkLabel(
            self, text="Готов к работе", font=ctk.CTkFont(size=13)
        )
        self._status_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Прогресс-бар
        self._progress_bar = ctk.CTkProgressBar(self, height=20)
        self._progress_bar.grid(row=1, column=0, sticky="ew")
        self._progress_bar.set(0)

        # Процент
        self._percent_label = ctk.CTkLabel(self, text="0%", font=ctk.CTkFont(size=12))
        self._percent_label.grid(row=2, column=0, sticky="e", pady=(5, 0))

    def update_progress(self, progress: ProgressInfo) -> None:
        """Обновить прогресс."""
        percent = progress.percentage / 100
        self._progress_bar.set(percent)
        self._percent_label.configure(text=f"{progress.percentage:.0f}%")
        self._status_label.configure(text=progress.message or "Обработка...")

    def reset(self) -> None:
        """Сбросить прогресс."""
        self._progress_bar.set(0)
        self._percent_label.configure(text="0%")
        self._status_label.configure(text="Готов к работе")

    def set_status(self, status: str) -> None:
        """Установить текст статуса."""
        self._status_label.configure(text=status)


class MainWindow(ctk.CTk):
    """
    Главное окно приложения.
    Отвечает за UI, ничего не знает о бизнес-логике.
    """

    def __init__(
        self,
        title: str = "Генератор документов",
        size: tuple[int, int] = (700, 500),
        default_output_dir: Path | None = None,
    ):
        super().__init__()

        # Настройка окна
        self.title(title)
        self.geometry(f"{size[0]}x{size[1]}")
        self.minsize(600, 450)

        # Тема
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Callback для генерации (будет установлен извне)
        self._on_generate: Callable | None = None
        self._on_cancel: Callable | None = None
        self._is_generating = False
        self._default_output_dir = default_output_dir

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Создать виджеты."""
        # Основной контейнер с отступами
        self._main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        self._main_frame.grid_columnconfigure(0, weight=1)

        # Заголовок
        self._title_label = ctk.CTkLabel(
            self._main_frame,
            text="📄 Генератор Word документов",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self._title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Выбор Excel файла
        self._excel_selector = FileSelector(
            self._main_frame,
            label="📊 Excel файл с данными:",
            filetypes=[("Excel файлы", "*.xlsx *.xls"), ("Все файлы", "*.*")],
        )
        self._excel_selector.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Выбор шаблона Word
        self._template_selector = FileSelector(
            self._main_frame,
            label="📝 Word шаблон:",
            filetypes=[("Word документы", "*.docx"), ("Все файлы", "*.*")],
        )
        self._template_selector.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        # Выбор папки для результатов
        self._output_selector = FolderSelector(
            self._main_frame,
            label="📁 Папка для результатов:",
            default_path=self._default_output_dir,
        )
        self._output_selector.grid(row=3, column=0, sticky="ew", pady=(0, 25))

        # Панель прогресса
        self._progress_panel = ProgressPanel(self._main_frame)
        self._progress_panel.grid(row=4, column=0, sticky="ew", pady=(0, 25))

        # Кнопки
        self._buttons_frame = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        self._buttons_frame.grid(row=5, column=0, sticky="ew")
        self._buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self._generate_button = ctk.CTkButton(
            self._buttons_frame,
            text="🚀 Сгенерировать",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            command=self._on_generate_click,
        )
        self._generate_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self._cancel_button = ctk.CTkButton(
            self._buttons_frame,
            text="❌ Отмена",
            font=ctk.CTkFont(size=15),
            height=45,
            fg_color="gray",
            hover_color="darkgray",
            command=self._on_cancel_click,
            state="disabled",
        )
        self._cancel_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        # Информация
        self._info_label = ctk.CTkLabel(
            self._main_frame,
            text="💡 Используйте переменные {{ название }} в Word шаблоне",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._info_label.grid(row=6, column=0, sticky="w", pady=(20, 0))

    def _on_generate_click(self) -> None:
        """Обработчик нажатия кнопки генерации."""
        # Проверяем выбор файлов
        if not self._excel_selector.file_path:
            messagebox.showwarning("Внимание", "Выберите Excel файл с данными")
            return

        if not self._template_selector.file_path:
            messagebox.showwarning("Внимание", "Выберите Word шаблон")
            return

        if not self._output_selector.folder_path:
            messagebox.showwarning("Внимание", "Выберите папку для результатов")
            return

        if self._on_generate:
            self._set_generating_state(True)
            self._on_generate(
                excel_path=self._excel_selector.file_path,
                template_path=self._template_selector.file_path,
                output_dir=self._output_selector.folder_path,
            )

    def _on_cancel_click(self) -> None:
        """Обработчик нажатия кнопки отмены."""
        if self._on_cancel:
            self._on_cancel()

    def _set_generating_state(self, is_generating: bool) -> None:
        """Установить состояние генерации."""
        self._is_generating = is_generating

        if is_generating:
            self._generate_button.configure(state="disabled")
            self._cancel_button.configure(state="normal")
        else:
            self._generate_button.configure(state="normal")
            self._cancel_button.configure(state="disabled")

    def set_on_generate(self, callback: Callable) -> None:
        """Установить callback для генерации."""
        self._on_generate = callback

    def set_on_cancel(self, callback: Callable) -> None:
        """Установить callback для отмены."""
        self._on_cancel = callback

    def update_progress(self, progress: ProgressInfo) -> None:
        """Обновить прогресс (thread-safe)."""
        self.after(0, lambda: self._progress_panel.update_progress(progress))

    def show_result(
        self, success: bool, message: str, output_dir: Path | None = None
    ) -> None:
        """Показать результат генерации."""
        self._set_generating_state(False)

        if success:
            self._progress_panel.set_status(message)
            result = messagebox.askyesno(
                "Готово!", f"{message}\n\nОткрыть папку с результатами?"
            )
            if result and output_dir:
                self._open_folder(output_dir)
        else:
            self._progress_panel.set_status("Ошибка")
            messagebox.showerror("Ошибка", message)

    def show_error(self, message: str) -> None:
        """Показать сообщение об ошибке."""
        self._set_generating_state(False)
        self._progress_panel.set_status("Ошибка")
        messagebox.showerror("Ошибка", message)

    def reset(self) -> None:
        """Сбросить состояние."""
        self._progress_panel.reset()
        self._set_generating_state(False)

    @staticmethod
    def _open_folder(path: Path) -> None:
        """Открыть папку в проводнике."""
        import platform
        import subprocess

        system = platform.system()

        if system == "Windows":
            subprocess.run(["explorer", str(path)])
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(path)])
        else:  # Linux
            subprocess.run(["xdg-open", str(path)])
