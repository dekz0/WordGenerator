@echo off
REM Скрипт сборки exe файла для Windows

echo 🔨 Сборка WordGenerator...

REM Устанавливаем зависимости
pip install -r requirements.txt

REM Собираем exe
pyinstaller WordGenerator.spec --clean

echo ✅ Готово! Исполняемый файл: dist\WordGenerator.exe
pause
