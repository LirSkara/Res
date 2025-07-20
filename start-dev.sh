#!/bin/bash

# QRes OS 4 - Development Start Script for Mac/Local Development
# ==============================================================

# Установка цветов для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🍽️  QRes OS 4 - Development Mode${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python не найден. Убедитесь, что Python 3 установлен.${NC}"
    exit 1
fi

# Переход в директорию проекта
cd "$(dirname "$0")" || exit

echo -e "${BLUE}📋 Проверка зависимостей...${NC}"

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}🔄 Создание виртуального окружения...${NC}"
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo -e "${YELLOW}🔄 Обновление зависимостей...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Проверка наличия .env файла для разработки
if [ ! -f ".env.dev" ]; then
    echo -e "${BLUE}⚙️  Создание .env.dev файла для разработки...${NC}"
    cat > ".env.dev" << EOF
# QRes OS 4 Development Environment
DEBUG=true
RELOAD=true
HOST=127.0.0.1
PORT=8000
LOG_LEVEL=debug

# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Security (для разработки)
SECRET_KEY=dev-secret-key-change-in-production

# Logging
LOG_DIR=./logs
EOF
    echo -e "${GREEN}✅ Файл .env.dev создан${NC}"
fi

# Применение миграций базы данных
echo -e "${BLUE}🔄 Применение миграций базы данных...${NC}"
python3 -m alembic upgrade head

# Загрузка переменных из .env.dev
export $(grep -v '^#' .env.dev | xargs)

echo -e "${BLUE}🚀 Запуск сервера на ${YELLOW}${HOST}:${PORT}${NC}"
echo -e "${BLUE}📝 Уровень логирования: ${YELLOW}${LOG_LEVEL}${NC}"
echo -e "${BLUE}⚙️  Режим отладки: ${YELLOW}${DEBUG}${NC}"
echo -e "${BLUE}🔄 Автоперезагрузка: ${YELLOW}${RELOAD}${NC}"
echo ""
echo -e "${GREEN}📚 Документация API доступна по адресу:${NC}"
echo -e "   ${YELLOW}http://${HOST}:${PORT}/docs${NC}"
echo -e "   ${YELLOW}http://${HOST}:${PORT}/redoc${NC}"
echo ""
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}💡 Нажмите Ctrl+C для остановки сервера${NC}"
echo -e "${BLUE}==================================================${NC}"

# Запуск сервера
python3 -m uvicorn app.main:app --host $HOST --port $PORT --log-level $LOG_LEVEL --reload
