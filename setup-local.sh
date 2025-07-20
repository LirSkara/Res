#!/bin/bash

# QRes OS 4 - Скрипт для запуска прямо из текущей директории
# =========================================================

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🚀 QRes OS 4 - Локальная установка${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Этот скрипт должен быть запущен с правами root (sudo)${NC}"
    exit 1
fi

# Получение текущего пути проекта (используем текущую директорию)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="$SCRIPT_DIR"

echo -e "${BLUE}📁 Устанавливаем прямо в текущую директорию: ${YELLOW}$PROJECT_PATH${NC}"
echo ""

# Проверка наличия основных файлов проекта
if [ ! -f "$PROJECT_PATH/app/main.py" ]; then
    echo -e "${RED}❌ Файл app/main.py не найден в текущей директории${NC}"
    echo -e "${BLUE}💡 Убедитесь, что запускаете скрипт из корня проекта QRes OS 4${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Проект найден в текущей директории${NC}"

# Установка Python зависимостей
echo -e "${BLUE}🐍 Проверка Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}🔄 Установка Python3...${NC}"
    apt update
    apt install -y python3 python3-pip python3-venv python3-full
fi

# Создание виртуального окружения
echo -e "${BLUE}🔧 Настройка виртуального окружения...${NC}"
if [ ! -d "$PROJECT_PATH/venv" ]; then
    cd "$PROJECT_PATH"
    python3 -m venv venv --system-site-packages 2>/dev/null || python3 -m venv venv
    echo -e "${GREEN}✅ Виртуальное окружение создано${NC}"
fi

# Активация виртуального окружения и установка зависимостей
echo -e "${BLUE}📦 Установка зависимостей...${NC}"
cd "$PROJECT_PATH"
source venv/bin/activate
pip install --upgrade pip 2>/dev/null || echo -e "${YELLOW}⚠️  Не удалось обновить pip${NC}"

# Попытка установки зависимостей
if ! pip install -r requirements.txt 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Пробуем установку с --break-system-packages...${NC}"
    if ! pip install -r requirements.txt --break-system-packages 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Устанавливаем минимальные зависимости...${NC}"
        pip install fastapi uvicorn sqlalchemy alembic aiosqlite python-jose passlib python-multipart python-dotenv pydantic pydantic-settings --break-system-packages 2>/dev/null || {
            echo -e "${RED}❌ Не удалось установить зависимости${NC}"
            exit 1
        }
    fi
fi
echo -e "${GREEN}✅ Зависимости установлены${NC}"

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
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Security
SECRET_KEY=\$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "change-this-secret-key-in-production")

# Logging
LOG_DIR=./logs
EOF
    echo -e "${GREEN}✅ Файл .env создан${NC}"
fi

# Создание systemd service файла
echo -e "${BLUE}⚙️  Создание systemd service...${NC}"
cat > /etc/systemd/system/qresos-backend.service << EOF
[Unit]
Description=QRes OS 4 Restaurant Management System Backend
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_PATH
Environment=PATH=$PROJECT_PATH/venv/bin
Environment=VIRTUAL_ENV=$PROJECT_PATH/venv
Environment=NODE_ENV=production
Environment=DEBUG=false
Environment=RELOAD=false
Environment=HOST=192.168.4.1
Environment=PORT=8000
Environment=LOG_LEVEL=info
ExecStartPre=/bin/bash -c 'cd $PROJECT_PATH && source venv/bin/activate && python3 -m alembic upgrade head'
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

# Создание скрипта управления
echo -e "${BLUE}🔧 Создание скрипта управления...${NC}"
cat > /usr/local/bin/qresos-control << EOF
#!/bin/bash
SERVICE_NAME="qresos-backend"
PROJECT_PATH="$PROJECT_PATH"
FIXED_IP="192.168.4.1"
PORT="8000"

case "\$1" in
    start)
        echo "🚀 Запуск QRes OS 4..."
        systemctl start \$SERVICE_NAME
        sleep 2
        echo "✅ QRes OS 4 запущен"
        ;;
    stop)
        echo "🛑 Остановка QRes OS 4..."
        systemctl stop \$SERVICE_NAME
        echo "✅ QRes OS 4 остановлен"
        ;;
    restart)
        echo "🔄 Перезапуск QRes OS 4..."
        systemctl restart \$SERVICE_NAME
        sleep 2
        echo "✅ QRes OS 4 перезапущен"
        ;;
    status)
        echo "📊 Статус QRes OS 4:"
        systemctl status \$SERVICE_NAME --no-pager
        ;;
    logs)
        echo "📋 Логи QRes OS 4:"
        journalctl -u \$SERVICE_NAME -f
        ;;
    info)
        echo "📡 Информация о QRes OS 4:"
        echo "   Путь к проекту: \$PROJECT_PATH"
        echo "   Пользователь: $USER"
        echo "   Фиксированный IP: \$FIXED_IP"
        echo "   Порт: \$PORT"
        echo ""
        echo "🌐 Доступные адреса:"
        echo "   🏠 Локально: http://localhost:\$PORT"
        echo "   📡 Фиксированный IP: http://\$FIXED_IP:\$PORT"
        echo "   📖 API документация: http://\$FIXED_IP:\$PORT/docs"
        ;;
    *)
        echo "Использование: qresos-control {start|stop|restart|status|logs|info}"
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/qresos-control

# Настройка прав доступа
echo -e "${BLUE}🔐 Настройка прав доступа...${NC}"
[ -f "$PROJECT_PATH/start.sh" ] && chmod +x "$PROJECT_PATH/start.sh"
[ -f "$PROJECT_PATH/stop.sh" ] && chmod +x "$PROJECT_PATH/stop.sh"
[ -f "$PROJECT_PATH/start-dev.sh" ] && chmod +x "$PROJECT_PATH/start-dev.sh"

# Перезагрузка systemd и включение сервиса
echo -e "${BLUE}🔄 Настройка автозапуска...${NC}"
systemctl daemon-reload
systemctl enable qresos-backend.service

# Запуск сервиса
echo -e "${BLUE}🚀 Запуск сервиса...${NC}"
systemctl start qresos-backend.service

# Проверка статуса
sleep 3
if systemctl is-active --quiet qresos-backend.service; then
    echo -e "${GREEN}✅ Сервис успешно запущен${NC}"
else
    echo -e "${RED}❌ Ошибка запуска сервиса${NC}"
    echo -e "${BLUE}📊 Логи сервиса:${NC}"
    journalctl -u qresos-backend.service --no-pager -l --since "5 minutes ago"
fi

echo ""
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🎉 Установка завершена!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""
echo -e "${GREEN}📋 Полезные команды:${NC}"
echo -e "   ${YELLOW}sudo qresos-control start${NC}      - запустить QRes OS 4"
echo -e "   ${YELLOW}sudo qresos-control stop${NC}       - остановить QRes OS 4"
echo -e "   ${YELLOW}sudo qresos-control status${NC}     - статус и логи"
echo -e "   ${YELLOW}sudo qresos-control info${NC}       - информация о проекте"
echo ""
echo -e "${GREEN}🌐 API будет доступен по адресу: ${YELLOW}http://192.168.4.1:8000${NC}"
echo -e "${GREEN}📚 Документация: ${YELLOW}http://192.168.4.1:8000/docs${NC}"
echo ""
echo -e "${GREEN}📁 Проект установлен в: ${YELLOW}$PROJECT_PATH${NC}"
echo ""
