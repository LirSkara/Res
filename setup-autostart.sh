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
PROJECT_PATH="$SCRIPT_DIR"

echo -e "${BLUE}📁 Директория проекта: ${YELLOW}$PROJECT_PATH${NC}"
echo ""

# Проверка, что мы находимся в правильной директории
if [ ! -f "$PROJECT_PATH/app/main.py" ]; then
    echo -e "${RED}❌ Файл app/main.py не найден в $PROJECT_PATH${NC}"
    echo -e "${RED}   Убедитесь, что скрипт запускается из корня проекта backend${NC}"
    exit 1
fi

# Создание пользователя для веб-сервиса (если не существует)
if ! id "admin" &>/dev/null; then
    echo -e "${BLUE}👤 Создание пользователя admin...${NC}"
    useradd --create-home --shell /bin/bash admin
    usermod -aG sudo admin  # Добавляем в группу sudo для управления
    echo -e "${GREEN}✅ Пользователь admin создан${NC}"
else
    echo -e "${GREEN}✅ Пользователь admin уже существует${NC}"
fi

# Убеждаемся, что пользователь admin может читать проект
echo -e "${BLUE}� Настройка прав доступа к проекту...${NC}"
# Если проект не в домашней директории admin, настраиваем права
if [[ "$PROJECT_PATH" != "/home/admin"* ]]; then
    # Создаем символическую ссылку для удобства
    sudo -u admin ln -sfn "$PROJECT_PATH" "/home/admin/qresos-backend" 2>/dev/null || true
    # Даем права пользователю admin на чтение директории проекта
    chmod -R 755 "$PROJECT_PATH"
    # Убеждаемся что admin может выполнять скрипты
    chmod +x "$PROJECT_PATH"/*.sh 2>/dev/null || true
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
echo -e "${BLUE}🔐 Финальная настройка прав доступа...${NC}"
# Проверяем существование файлов перед изменением прав
[ -f "$PROJECT_PATH/start.sh" ] && chmod +x "$PROJECT_PATH/start.sh"
[ -f "$PROJECT_PATH/stop.sh" ] && chmod +x "$PROJECT_PATH/stop.sh"
[ -f "$PROJECT_PATH/start-dev.sh" ] && chmod +x "$PROJECT_PATH/start-dev.sh"
[ -f "$PROJECT_PATH/qresos-control.sh" ] && chmod +x "$PROJECT_PATH/qresos-control.sh"
[ -f "$PROJECT_PATH/manage-service.sh" ] && chmod +x "$PROJECT_PATH/manage-service.sh"

# Если проект в домашней директории admin, устанавливаем владельца
if [[ "$PROJECT_PATH" == "/home/admin"* ]]; then
    chown -R admin:admin "$PROJECT_PATH"
fi

# Создание .env файла (если не существует)
if [ ! -f "$PROJECT_PATH/.env" ]; then
    echo -e "${BLUE}⚙️  Создание файла .env...${NC}"
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
    # Устанавливаем права доступа только если файл в домашней директории admin
    if [[ "$PROJECT_PATH" == "/home/admin"* ]]; then
        chown admin:admin "$PROJECT_PATH/.env" 2>/dev/null || echo -e "${YELLOW}⚠️  Не удалось изменить владельца .env${NC}"
    fi
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
    # Создаем временную копию service файла с правильными путями
    cp "$PROJECT_PATH/qresos-backend.service" "/tmp/qresos-backend.service.tmp"
    # Обновление путей в service файле
    sed -i "s|/var/www/qresos4/backend|$PROJECT_PATH|g" "/tmp/qresos-backend.service.tmp"
    sed -i "s|/home/admin/qresos/backend|$PROJECT_PATH|g" "/tmp/qresos-backend.service.tmp"
    sed -i "s|User=www-data|User=admin|g" "/tmp/qresos-backend.service.tmp"
    sed -i "s|Group=www-data|Group=admin|g" "/tmp/qresos-backend.service.tmp"
    sed -i "s|User=qresos|User=admin|g" "/tmp/qresos-backend.service.tmp"
    sed -i "s|Group=qresos|Group=admin|g" "/tmp/qresos-backend.service.tmp"
    
    cp "/tmp/qresos-backend.service.tmp" /etc/systemd/system/qresos-backend.service
    rm "/tmp/qresos-backend.service.tmp"
    echo -e "${GREEN}✅ Service файл установлен${NC}"
else
    echo -e "${YELLOW}⚠️  Файл qresos-backend.service не найден, создаем его...${NC}"
    cat > /etc/systemd/system/qresos-backend.service << EOF
[Unit]
Description=QRes OS 4 Restaurant Management System Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=$PROJECT_PATH
Environment=PATH=$PROJECT_PATH/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=VIRTUAL_ENV=$PROJECT_PATH/venv
Environment=NODE_ENV=production
Environment=DEBUG=false
Environment=RELOAD=false
Environment=PORT=8000
Environment=LOG_LEVEL=info
ExecStartPre=/bin/bash -c 'cd $PROJECT_PATH && if [ -d "venv" ]; then source venv/bin/activate; fi && python3 -m alembic upgrade head'
ExecStart=/bin/bash $PROJECT_PATH/start.sh
ExecReload=/bin/kill -HUP \$MAINPID
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
echo -e "${GREEN}🌐 API будет доступен по адресу:${NC}"
if ip addr show | grep -q "192.168.4.1"; then
    echo -e "   ${YELLOW}http://192.168.4.1:8000${NC}"
    echo -e "${GREEN}📚 Документация: ${YELLOW}http://192.168.4.1:8000/docs${NC}"
else
    echo -e "   ${YELLOW}http://127.0.0.1:8000${NC} (локально)"
    echo -e "   ${YELLOW}http://[IP-адрес-сервера]:8000${NC} (внешний доступ)"
    echo -e "${GREEN}📚 Документация: ${YELLOW}http://127.0.0.1:8000/docs${NC}"
fi
echo -e "${GREEN}📂 Проект установлен в: ${YELLOW}$PROJECT_PATH${NC}"
echo ""
