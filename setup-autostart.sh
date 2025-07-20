#!/bin/bash

# QRes OS 4 - Autostart Setup Script for Ubuntu Server 24
# ========================================================

# Установка цветов для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Этот скрипт должен быть запущен с правами root (sudo)${NC}"
    exit 1
fi

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🔧 QRes OS 4 - Настройка автостарта${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Получение текущего пути проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="/var/www/qresos4/backend"

echo -e "${BLUE}📁 Текущая директория скрипта: ${YELLOW}$SCRIPT_DIR${NC}"
echo -e "${BLUE}📁 Целевая директория проекта: ${YELLOW}$PROJECT_PATH${NC}"
echo ""

# Создание пользователя для веб-сервиса (если не существует)
if ! id "qresos" &>/dev/null; then
    echo -e "${BLUE}👤 Создание пользователя qresos...${NC}"
    useradd --system --home /var/www/qresos4 --shell /bin/bash qresos
    echo -e "${GREEN}✅ Пользователь qresos создан${NC}"
else
    echo -e "${GREEN}✅ Пользователь qresos уже существует${NC}"
fi

# Создание директории проекта
echo -e "${BLUE}📁 Создание директорий...${NC}"
mkdir -p /var/www/qresos4
mkdir -p /var/log/qresos4

# Копирование файлов проекта
if [ "$SCRIPT_DIR" != "$PROJECT_PATH" ]; then
    echo -e "${BLUE}📋 Копирование файлов проекта...${NC}"
    cp -r "$SCRIPT_DIR/"* "$PROJECT_PATH/"
    echo -e "${GREEN}✅ Файлы проекта скопированы${NC}"
fi

# Установка Python и зависимостей
echo -e "${BLUE}🐍 Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}🔄 Установка Python3...${NC}"
    apt update
    apt install -y python3 python3-pip python3-venv
fi

# Установка PostgreSQL (если требуется)
echo -e "${BLUE}🗄️ Проверка PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL не найден. Установите его при необходимости:${NC}"
    echo -e "   ${YELLOW}sudo apt install postgresql postgresql-contrib${NC}"
fi

# Создание виртуального окружения
echo -e "${BLUE}🔧 Настройка виртуального окружения...${NC}"
cd "$PROJECT_PATH"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
fi

# Активация виртуального окружения и установка зависимостей
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✅ Зависимости установлены${NC}"

# Настройка прав доступа
echo -e "${BLUE}🔐 Настройка прав доступа...${NC}"
chown -R qresos:qresos /var/www/qresos4
chown -R qresos:qresos /var/log/qresos4
chmod +x "$PROJECT_PATH/start.sh"
chmod +x "$PROJECT_PATH/stop.sh"

# Создание .env файла (если не существует)
if [ ! -f "$PROJECT_PATH/.env" ]; then
    echo -e "${BLUE}⚙️  Создание файла .env...${NC}"
    cat > "$PROJECT_PATH/.env" << EOF
# QRes OS 4 Environment Configuration
DEBUG=false
RELOAD=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Logging
LOG_DIR=/var/log/qresos4
EOF
    chown qresos:qresos "$PROJECT_PATH/.env"
    echo -e "${GREEN}✅ Файл .env создан${NC}"
fi

# Копирование systemd service файла
echo -e "${BLUE}⚙️  Установка systemd service...${NC}"
if [ -f "$PROJECT_PATH/qresos-backend.service" ]; then
    # Обновление путей в service файле
    sed -i "s|/var/www/qresos4/backend|$PROJECT_PATH|g" "$PROJECT_PATH/qresos-backend.service"
    sed -i "s|User=www-data|User=qresos|g" "$PROJECT_PATH/qresos-backend.service"
    sed -i "s|Group=www-data|Group=qresos|g" "$PROJECT_PATH/qresos-backend.service"
    
    cp "$PROJECT_PATH/qresos-backend.service" /etc/systemd/system/
    echo -e "${GREEN}✅ Service файл установлен${NC}"
else
    echo -e "${RED}❌ Файл qresos-backend.service не найден${NC}"
    exit 1
fi

# Перезагрузка systemd и включение автостарта
echo -e "${BLUE}🔄 Настройка автостарта...${NC}"
systemctl daemon-reload
systemctl enable qresos-backend.service
echo -e "${GREEN}✅ Автостарт настроен${NC}"

# Запуск сервиса
echo -e "${BLUE}🚀 Запуск сервиса...${NC}"
systemctl start qresos-backend.service

# Проверка статуса
sleep 3
if systemctl is-active --quiet qresos-backend.service; then
    echo -e "${GREEN}✅ Сервис успешно запущен${NC}"
    echo -e "${BLUE}📊 Статус сервиса:${NC}"
    systemctl status qresos-backend.service --no-pager -l
else
    echo -e "${RED}❌ Ошибка запуска сервиса${NC}"
    echo -e "${BLUE}📊 Логи сервиса:${NC}"
    journalctl -u qresos-backend.service --no-pager -l --since "5 minutes ago"
fi

echo ""
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🎉 Настройка автостарта завершена!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""
echo -e "${GREEN}📋 Полезные команды:${NC}"
echo -e "   ${YELLOW}sudo systemctl status qresos-backend${NC}     - проверить статус"
echo -e "   ${YELLOW}sudo systemctl start qresos-backend${NC}      - запустить сервис"
echo -e "   ${YELLOW}sudo systemctl stop qresos-backend${NC}       - остановить сервис"
echo -e "   ${YELLOW}sudo systemctl restart qresos-backend${NC}    - перезапустить сервис"
echo -e "   ${YELLOW}sudo systemctl disable qresos-backend${NC}    - отключить автостарт"
echo -e "   ${YELLOW}sudo journalctl -u qresos-backend -f${NC}     - просмотр логов в реальном времени"
echo ""
echo -e "${GREEN}🌐 API будет доступен по адресу: ${YELLOW}http://localhost:8000${NC}"
echo -e "${GREEN}📚 Документация: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
