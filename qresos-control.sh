#!/bin/bash

# QRes OS 4 - Скрипт управления проектом
# ========================================

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SERVICE_NAME="qresos-backend"
PROJECT_PATH="/var/www/qresos4/backend"
FIXED_IP="192.168.4.1"
PORT="8000"

case "$1" in
    start)
        echo -e "${GREEN}🚀 Запуск QRes OS 4...${NC}"
        systemctl start $SERVICE_NAME
        sleep 2
        echo -e "${GREEN}✅ QRes OS 4 запущен${NC}"
        ;;
    stop)
        echo -e "${YELLOW}🛑 Остановка QRes OS 4...${NC}"
        systemctl stop $SERVICE_NAME
        echo -e "${GREEN}✅ QRes OS 4 остановлен${NC}"
        ;;
    restart)
        echo -e "${BLUE}🔄 Перезапуск QRes OS 4...${NC}"
        systemctl restart $SERVICE_NAME
        sleep 2
        echo -e "${GREEN}✅ QRes OS 4 перезапущен${NC}"
        ;;
    status)
        echo -e "${CYAN}📊 Статус QRes OS 4:${NC}"
        systemctl status $SERVICE_NAME --no-pager
        echo ""
        echo -e "${CYAN}📊 Логи (последние 20 строк):${NC}"
        journalctl -u $SERVICE_NAME -n 20 --no-pager
        ;;
    logs)
        echo -e "${CYAN}📋 Логи QRes OS 4:${NC}"
        journalctl -u $SERVICE_NAME -f
        ;;
    enable)
        echo -e "${BLUE}🔧 Включение автозапуска...${NC}"
        systemctl enable $SERVICE_NAME
        echo -e "${GREEN}✅ Автозапуск включен${NC}"
        ;;
    disable)
        echo -e "${BLUE}🔧 Отключение автозапуска...${NC}"
        systemctl disable $SERVICE_NAME
        echo -e "${GREEN}✅ Автозапуск отключен${NC}"
        ;;
    info)
        echo -e "${CYAN}📡 Информация о QRes OS 4:${NC}"
        echo -e "   Путь к проекту: $PROJECT_PATH"
        echo -e "   Пользователь: qresos"
        echo -e "   Фиксированный IP: $FIXED_IP"
        echo -e "   Порт: $PORT"
        echo -e "   Автозапуск: $(systemctl is-enabled $SERVICE_NAME 2>/dev/null || echo 'отключен')"
        echo ""
        echo -e "${GREEN}🌐 Доступные адреса:${NC}"
        echo -e "   🏠 Локально: http://localhost:$PORT"
        echo -e "   📡 Фиксированный IP: http://$FIXED_IP:$PORT"
        echo ""
        echo -e "${GREEN}📱 Интерфейсы:${NC}"
        echo -e "   📖 API документация: http://$FIXED_IP:$PORT/docs"
        echo -e "   📋 ReDoc: http://$FIXED_IP:$PORT/redoc"
        echo -e "   🔧 Admin панель: http://$FIXED_IP:$PORT/admin (если доступна)"
        ;;
    migrate)
        echo -e "${BLUE}🔄 Применение миграций базы данных...${NC}"
        cd $PROJECT_PATH
        source venv/bin/activate
        python3 -m alembic upgrade head
        echo -e "${GREEN}✅ Миграции применены${NC}"
        ;;
    create-admin)
        echo -e "${BLUE}👤 Создание администратора...${NC}"
        cd $PROJECT_PATH
        source venv/bin/activate
        python3 create_admin.py
        echo -e "${GREEN}✅ Готово${NC}"
        ;;
    backup)
        echo -e "${BLUE}💾 Создание резервной копии базы данных...${NC}"
        BACKUP_DIR="/var/backups/qresos4"
        mkdir -p $BACKUP_DIR
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        cp "$PROJECT_PATH/app.db" "$BACKUP_DIR/app_backup_$TIMESTAMP.db"
        echo -e "${GREEN}✅ Резервная копия создана: $BACKUP_DIR/app_backup_$TIMESTAMP.db${NC}"
        ;;
    *)
        echo -e "${CYAN}Использование: qresos-control {start|stop|restart|status|logs|enable|disable|info|migrate|create-admin|backup}${NC}"
        echo ""
        echo -e "${GREEN}Команды:${NC}"
        echo -e "  ${YELLOW}start${NC}        - Запустить QRes OS 4"
        echo -e "  ${YELLOW}stop${NC}         - Остановить QRes OS 4"
        echo -e "  ${YELLOW}restart${NC}      - Перезапустить QRes OS 4"
        echo -e "  ${YELLOW}status${NC}       - Показать статус и последние логи"
        echo -e "  ${YELLOW}logs${NC}         - Показать логи в реальном времени"
        echo -e "  ${YELLOW}enable${NC}       - Включить автозапуск при загрузке"
        echo -e "  ${YELLOW}disable${NC}      - Отключить автозапуск"
        echo -e "  ${YELLOW}info${NC}         - Показать информацию о проекте"
        echo -e "  ${YELLOW}migrate${NC}      - Применить миграции базы данных"
        echo -e "  ${YELLOW}create-admin${NC} - Создать администратора"
        echo -e "  ${YELLOW}backup${NC}       - Создать резервную копию БД"
        exit 1
        ;;
esac
