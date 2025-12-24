#!/bin/bash
# Скрипт сборки exe файла

echo "🔨 Сборка WordGenerator..."

# Устанавливаем зависимости
pip install -r requirements.txt

# Собираем exe
pyinstaller WordGenerator.spec --clean

echo "✅ Готово! Исполняемый файл: dist/WordGenerator"
