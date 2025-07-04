#!/bin/bash

# QRes OS 4 - Startup Script
echo "🍽️ QRes OS 4 - Restaurant Management System"
echo "============================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8+"
    exit 1
fi

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден. Установите pip3"
    exit 1
fi

# Создание виртуального окружения (если не существует)
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📚 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверка файла .env
if [ ! -f ".env" ]; then
    echo "⚙️ Создание файла .env..."
    cp .env .env.local 2>/dev/null || echo "Создайте файл .env на основе .env"
fi

# Инициализация базы данных
echo "🗄️ Инициализация базы данных..."
python init_db.py

# Запуск сервера
echo "🚀 Запуск QRes OS 4..."
echo "API будет доступно на: http://localhost:8000"
echo "Документация API: http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
