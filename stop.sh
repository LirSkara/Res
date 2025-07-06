#!/bin/bash

# QRes OS 4 - Stop Server Script
# -----------------------------------------

# Установка цветов для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${RED}🛑 QRes OS 4 - Остановка сервера${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Ищем процесс uvicorn
PID=$(pgrep -f "uvicorn app.main:app")

if [ -z "$PID" ]; then
    echo -e "${YELLOW}⚠️  Сервер QRes OS 4 не запущен${NC}"
    exit 0
fi

echo -e "${BLUE}🔍 Найден процесс сервера с PID: ${YELLOW}$PID${NC}"
echo -e "${BLUE}🔄 Отправка сигнала завершения...${NC}"

# Отправляем сигнал завершения
kill -15 "$PID"

# Проверяем, остановился ли процесс
sleep 2
if ps -p "$PID" > /dev/null; then
    echo -e "${YELLOW}⚠️  Сервер не отвечает на сигнал завершения. Принудительное завершение...${NC}"
    kill -9 "$PID"
    sleep 1
fi

# Проверяем еще раз
if ! ps -p "$PID" > /dev/null; then
    echo -e "${GREEN}✅ Сервер успешно остановлен${NC}"
else
    echo -e "${RED}❌ Не удалось остановить сервер${NC}"
    exit 1
fi

echo -e "${BLUE}==================================================${NC}"
