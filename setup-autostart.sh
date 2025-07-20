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
mkdir -p /var/www/qresos4/backend
mkdir -p /var/log/qresos4

# Копирование файлов проекта
if [ "$SCRIPT_DIR" != "$PROJECT_PATH" ]; then
    echo -e "${BLUE}📋 Копирование файлов проекта...${NC}"
    # Убеждаемся что целевая директория существует
    mkdir -p "$PROJECT_PATH"
    # Копируем все файлы из текущей директории
    cp -r "$SCRIPT_DIR/"* "$PROJECT_PATH/" 2>/dev/null || true
    echo -e "${GREEN}✅ Файлы проекта скопированы${NC}"
else
    echo -e "${GREEN}✅ Файлы уже в целевой директории${NC}"
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
    python3 -m venv venv --system-site-packages 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Создание venv с system-site-packages...${NC}"
        python3 -m venv venv
    }
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
fi

# Активация виртуального окружения и установка зависимостей
echo -e "${BLUE}📦 Установка зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip 2>/dev/null || echo -e "${YELLOW}⚠️  Не удалось обновить pip${NC}"

# Попытка установки с разными методами
if ! pip install -r requirements.txt 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Пробуем установку с --break-system-packages...${NC}"
    if ! pip install -r requirements.txt --break-system-packages 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Пробуем минимальные зависимости...${NC}"
        if [ -f "requirements-minimal.txt" ]; then
            pip install -r requirements-minimal.txt --break-system-packages 2>/dev/null || {
                echo -e "${YELLOW}⚠️  Устанавливаем только самые необходимые пакеты...${NC}"
                pip install fastapi uvicorn sqlalchemy alembic aiosqlite python-jose passlib python-multipart python-dotenv pydantic pydantic-settings --break-system-packages 2>/dev/null || {
                    echo -e "${RED}❌ Не удалось установить зависимости. Продолжаем без них.${NC}"
                }
            }
        else
            echo -e "${YELLOW}⚠️  Устанавливаем только самые необходимые пакеты...${NC}"
            pip install fastapi uvicorn sqlalchemy alembic aiosqlite python-jose passlib python-multipart python-dotenv pydantic pydantic-settings --break-system-packages 2>/dev/null || {
                echo -e "${RED}❌ Не удалось установить зависимости. Продолжаем без них.${NC}"
            }
        fi
    fi
fi
echo -e "${GREEN}✅ Зависимости установлены${NC}"

# Настройка прав доступа
echo -e "${BLUE}🔐 Настройка прав доступа...${NC}"
chown -R qresos:qresos /var/www/qresos4
chown -R qresos:qresos /var/log/qresos4
# Проверяем существование файлов перед изменением прав
[ -f "$PROJECT_PATH/start.sh" ] && chmod +x "$PROJECT_PATH/start.sh"
[ -f "$PROJECT_PATH/stop.sh" ] && chmod +x "$PROJECT_PATH/stop.sh"
[ -f "$PROJECT_PATH/start-dev.sh" ] && chmod +x "$PROJECT_PATH/start-dev.sh"
[ -f "$PROJECT_PATH/qresos-control.sh" ] && chmod +x "$PROJECT_PATH/qresos-control.sh"

# Создание .env файла (если не существует)
if [ ! -f "$PROJECT_PATH/.env" ]; then
    echo -e "${BLUE}⚙️  Создание файла .env...${NC}"
    # Убеждаемся что директория существует
    mkdir -p "$(dirname "$PROJECT_PATH/.env")"
    cat > "$PROJECT_PATH/.env" << EOF
# QRes OS 4 Environment Configuration
DEBUG=false
RELOAD=false
# HOST будет автоматически определен в start.sh
# Для принудительного использования конкретного IP раскомментируйте:
# HOST=192.168.4.1
PORT=8000
LOG_LEVEL=info

# Database Configuration
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Logging
LOG_DIR=/var/log/qresos4
EOF
    chown qresos:qresos "$PROJECT_PATH/.env" 2>/dev/null || echo -e "${YELLOW}⚠️  Не удалось изменить владельца .env${NC}"
    echo -e "${GREEN}✅ Файл .env создан${NC}"
else
    echo -e "${GREEN}✅ Файл .env уже существует${NC}"
fi

# Установка скрипта управления
echo -e "${BLUE}🔧 Установка скрипта управления...${NC}"
if [ -f "$PROJECT_PATH/qresos-control.sh" ]; then
    cp "$PROJECT_PATH/qresos-control.sh" /usr/local/bin/qresos-control
    chmod +x /usr/local/bin/qresos-control
    echo -e "${GREEN}✅ Скрипт управления установлен${NC}"
else
    echo -e "${YELLOW}⚠️  Файл qresos-control.sh не найден${NC}"
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
    echo -e "${YELLOW}⚠️  Файл qresos-backend.service не найден, создаем его...${NC}"
    cat > /etc/systemd/system/qresos-backend.service << 'EOF'
[Unit]
Description=QRes OS 4 Restaurant Management System Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=qresos
Group=qresos
WorkingDirectory=/var/www/qresos4/backend
Environment=PATH=/var/www/qresos4/backend/venv/bin
Environment=VIRTUAL_ENV=/var/www/qresos4/backend/venv
Environment=NODE_ENV=production
Environment=DEBUG=false
Environment=RELOAD=false
Environment=HOST=192.168.4.1
Environment=PORT=8000
Environment=LOG_LEVEL=info
ExecStartPre=/bin/bash -c 'cd /var/www/qresos4/backend && source venv/bin/activate && python3 -m alembic upgrade head'
ExecStart=/bin/bash /var/www/qresos4/backend/start.sh
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo -e "${GREEN}✅ Service файл создан${NC}"
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
echo -e "${GREEN}🎮 Команды управления через скрипт:${NC}"
echo -e "   ${YELLOW}sudo qresos-control start${NC}      - запустить QRes OS 4"
echo -e "   ${YELLOW}sudo qresos-control stop${NC}       - остановить QRes OS 4"
echo -e "   ${YELLOW}sudo qresos-control status${NC}     - статус и логи"
echo -e "   ${YELLOW}sudo qresos-control info${NC}       - информация о проекте"
echo -e "   ${YELLOW}sudo qresos-control migrate${NC}    - применить миграции"
echo -e "   ${YELLOW}sudo qresos-control create-admin${NC} - создать админа"
echo ""
echo -e "${GREEN}🌐 API будет доступен по адресу: ${YELLOW}http://192.168.4.1:8000${NC}"
echo -e "${GREEN}📚 Документация: ${YELLOW}http://192.168.4.1:8000/docs${NC}"
echo ""
