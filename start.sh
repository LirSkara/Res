#!/bin/bash

# QRes OS 4 - Start Server Script
# -----------------------------------------

# Установка цветов для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🍽️  QRes OS 4 - Restaurant Management System${NC}"
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
# Установка зависимостей, если они еще не установлены
if [[ "$1" == "--install" ]]; then
    echo -e "${YELLOW}🔄 Устанавливаем зависимости...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Зависимости установлены${NC}"
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env файл не найден, будут использованы значения по умолчанию${NC}"
fi

# Применение миграций базы данных
echo -e "${BLUE}🔄 Применение миграций базы данных...${NC}"
python3 -m alembic upgrade head

# Определение параметров запуска
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
LOG_LEVEL=${LOG_LEVEL:-info}
DEBUG=${DEBUG:-true}
RELOAD=${RELOAD:-true}

echo -e "${BLUE}🚀 Запуск сервера на ${YELLOW}${HOST}:${PORT}${NC}"
echo -e "${BLUE}📝 Уровень логирования: ${YELLOW}${LOG_LEVEL}${NC}"
echo -e "${BLUE}⚙️  Режим отладки: ${YELLOW}${DEBUG}${NC}"
echo -e "${BLUE}🔄 Автоперезагрузка: ${YELLOW}${RELOAD}${NC}"
echo ""
echo -e "${GREEN}📚 Документация API доступна по адресу:${NC}"
echo -e "   ${YELLOW}http://localhost:${PORT}/docs${NC}"
echo -e "   ${YELLOW}http://localhost:${PORT}/redoc${NC}"
echo ""
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}💡 Нажмите Ctrl+C для остановки сервера${NC}"
echo -e "${BLUE}==================================================${NC}"

# Запуск сервера
if [ "$RELOAD" = "true" ]; then
    RELOAD_FLAG="--reload"
else
    RELOAD_FLAG=""
fi

python3 -m uvicorn app.main:app --host $HOST --port $PORT --log-level $LOG_LEVEL $RELOAD_FLAG
