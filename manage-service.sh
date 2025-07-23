#!/bin/bash

# QRes OS 4 - Service Management Script
# ====================================

# Устанshow_logs() {
    check_service_exists
    echo -e "${BLUE}📝 Логи сервиса $SERVICE_NAME:${NC}"
    echo -e "${YELLOW}Нажмите Ctrl+C для выхода${NC}"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -f
}

show_project_info() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${GREEN}🍽️  QRes OS 4 - Информация о проекте${NC}"
    echo -e "${BLUE}==================================================${NC}"
    echo ""
    
    # Получаем информацию о сервисе
    if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        PROJECT_PATH=$(systemctl show "$SERVICE_NAME" -p WorkingDirectory --value 2>/dev/null || echo "Не определен")
        echo -e "${GREEN}📂 Путь к проекту: ${YELLOW}$PROJECT_PATH${NC}"
        
        if [ -f "$PROJECT_PATH/.env" ]; then
            PORT=$(grep "^PORT=" "$PROJECT_PATH/.env" 2>/dev/null | cut -d'=' -f2 || echo "8000")
            echo -e "${GREEN}🌐 Порт: ${YELLOW}$PORT${NC}"
        fi
        
        # Проверяем доступность API
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            echo -e "${GREEN}📡 API доступен по адресу:${NC}"
            if ip addr show | grep -q "192.168.4.1"; then
                echo -e "   ${YELLOW}http://192.168.4.1:${PORT:-8000}${NC}"
                echo -e "   ${YELLOW}http://192.168.4.1:${PORT:-8000}/docs${NC} (документация)"
            else
                echo -e "   ${YELLOW}http://127.0.0.1:${PORT:-8000}${NC}"
                echo -e "   ${YELLOW}http://127.0.0.1:${PORT:-8000}/docs${NC} (документация)"
            fi
        else
            echo -e "${RED}❌ API недоступен (сервис остановлен)${NC}"
        fi
    else
        echo -e "${RED}❌ Сервис не установлен${NC}"
    fi
    echo ""
}етов для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SERVICE_NAME="qresos-backend"

show_help() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${GREEN}🔧 QRes OS 4 - Управление сервисом${NC}"
    echo -e "${BLUE}==================================================${NC}"
    echo ""
    echo -e "${GREEN}Использование:${NC}"
    echo -e "  ${YELLOW}$0 [команда]${NC}"
    echo ""
    echo -e "${GREEN}Доступные команды:${NC}"
    echo -e "  ${YELLOW}start${NC}     - Запустить сервис"
    echo -e "  ${YELLOW}stop${NC}      - Остановить сервис"
    echo -e "  ${YELLOW}restart${NC}   - Перезапустить сервис"
    echo -e "  ${YELLOW}status${NC}    - Показать статус сервиса"
    echo -e "  ${YELLOW}logs${NC}      - Показать логи сервиса"
    echo -e "  ${YELLOW}enable${NC}    - Включить автостарт"
    echo -e "  ${YELLOW}disable${NC}   - Отключить автостарт"
    echo -e "  ${YELLOW}info${NC}      - Показать информацию о проекте"
    echo -e "  ${YELLOW}install${NC}   - Установить/переустановить сервис"
    echo -e "  ${YELLOW}uninstall${NC} - Удалить сервис"
    echo -e "  ${YELLOW}help${NC}      - Показать эту справку"
    echo ""
}

check_service_exists() {
    if ! systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
        echo -e "${RED}❌ Сервис $SERVICE_NAME не установлен${NC}"
        echo -e "${YELLOW}💡 Запустите: sudo ./setup-autostart.sh${NC}"
        exit 1
    fi
}

start_service() {
    check_service_exists
    echo -e "${BLUE}🚀 Запуск сервиса $SERVICE_NAME...${NC}"
    if sudo systemctl start "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Сервис успешно запущен${NC}"
        sleep 2
        show_status
    else
        echo -e "${RED}❌ Ошибка запуска сервиса${NC}"
        exit 1
    fi
}

stop_service() {
    check_service_exists
    echo -e "${BLUE}🛑 Остановка сервиса $SERVICE_NAME...${NC}"
    if sudo systemctl stop "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Сервис успешно остановлен${NC}"
    else
        echo -e "${RED}❌ Ошибка остановки сервиса${NC}"
        exit 1
    fi
}

restart_service() {
    check_service_exists
    echo -e "${BLUE}🔄 Перезапуск сервиса $SERVICE_NAME...${NC}"
    if sudo systemctl restart "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Сервис успешно перезапущен${NC}"
        sleep 2
        show_status
    else
        echo -e "${RED}❌ Ошибка перезапуска сервиса${NC}"
        exit 1
    fi
}

show_status() {
    check_service_exists
    echo -e "${BLUE}📊 Статус сервиса $SERVICE_NAME:${NC}"
    sudo systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}🟢 Сервис работает${NC}"
    else
        echo -e "${RED}🔴 Сервис остановлен${NC}"
    fi
    
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}🔄 Автостарт включен${NC}"
    else
        echo -e "${YELLOW}⚠️  Автостарт отключен${NC}"
    fi
}

show_logs() {
    check_service_exists
    echo -e "${BLUE}📝 Логи сервиса $SERVICE_NAME:${NC}"
    echo -e "${YELLOW}(Нажмите Ctrl+C для выхода)${NC}"
    echo ""
    sudo journalctl -u "$SERVICE_NAME" -f --no-pager
}

enable_autostart() {
    check_service_exists
    echo -e "${BLUE}🔄 Включение автостарта для $SERVICE_NAME...${NC}"
    if sudo systemctl enable "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Автостарт включен${NC}"
    else
        echo -e "${RED}❌ Ошибка включения автостарта${NC}"
        exit 1
    fi
}

disable_autostart() {
    check_service_exists
    echo -e "${BLUE}⏸️  Отключение автостарта для $SERVICE_NAME...${NC}"
    if sudo systemctl disable "$SERVICE_NAME"; then
        echo -e "${GREEN}✅ Автостарт отключен${NC}"
    else
        echo -e "${RED}❌ Ошибка отключения автостарта${NC}"
        exit 1
    fi
}

install_service() {
    echo -e "${BLUE}🔧 Установка сервиса $SERVICE_NAME...${NC}"
    if [ -f "./setup-autostart.sh" ]; then
        sudo ./setup-autostart.sh
    else
        echo -e "${RED}❌ Файл setup-autostart.sh не найден${NC}"
        exit 1
    fi
}

uninstall_service() {
    echo -e "${BLUE}🗑️  Удаление сервиса $SERVICE_NAME...${NC}"
    
    # Остановка сервиса
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        sudo systemctl stop "$SERVICE_NAME"
        echo -e "${GREEN}✅ Сервис остановлен${NC}"
    fi
    
    # Отключение автостарта
    if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        sudo systemctl disable "$SERVICE_NAME"
        echo -e "${GREEN}✅ Автостарт отключен${NC}"
    fi
    
    # Удаление service файла
    if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
        sudo rm "/etc/systemd/system/$SERVICE_NAME.service"
        echo -e "${GREEN}✅ Service файл удален${NC}"
    fi
    
    # Перезагрузка systemd
    sudo systemctl daemon-reload
    echo -e "${GREEN}✅ Сервис полностью удален${NC}"
}

# Основная логика
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    enable)
        enable_autostart
        ;;
    disable)
        disable_autostart
        ;;
    info)
        show_project_info
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Неизвестная команда: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
