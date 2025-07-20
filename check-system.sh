#!/bin/bash

# QRes OS 4 - Проверка системы перед установкой
# ==============================================

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}🔍 QRes OS 4 - Проверка системы${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Проверка ОС
echo -e "${BLUE}📋 Информация о системе:${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "   OS: $PRETTY_NAME"
else
    echo -e "   OS: $(uname -s)"
fi
echo -e "   Архитектура: $(uname -m)"
echo -e "   Ядро: $(uname -r)"
echo ""

# Проверка Python
echo -e "${BLUE}🐍 Проверка Python:${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "   ✅ $PYTHON_VERSION"
    
    # Проверка версии Python
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo -e "   ✅ Версия Python подходит (требуется 3.9+)"
    else
        echo -e "   ❌ Версия Python слишком старая (требуется 3.9+)"
    fi
    
    # Проверка pip
    if command -v pip3 &> /dev/null; then
        echo -e "   ✅ pip3 доступен"
    else
        echo -e "   ❌ pip3 не найден"
    fi
    
    # Проверка venv
    if python3 -m venv --help &> /dev/null; then
        echo -e "   ✅ venv модуль доступен"
    else
        echo -e "   ❌ venv модуль не найден"
        echo -e "   💡 Установите: sudo apt install python3-venv"
    fi
else
    echo -e "   ❌ Python3 не найден"
    echo -e "   💡 Установите: sudo apt install python3 python3-pip python3-venv"
fi
echo ""

# Проверка сети
echo -e "${BLUE}🌐 Проверка сети:${NC}"
if command -v ip &> /dev/null; then
    echo -e "   📡 Сетевые интерфейсы:"
    ip addr show | grep -E "inet [0-9]" | awk '{print "      " $2}' | head -5
    
    # Проверка наличия IP 192.168.4.1
    if ip addr show | grep -q "192.168.4.1"; then
        echo -e "   ✅ IP 192.168.4.1 настроен"
    else
        echo -e "   ⚠️  IP 192.168.4.1 не настроен"
        echo -e "   💡 Будет использован локальный IP для разработки"
    fi
else
    echo -e "   ❌ ip команда не найдена"
fi
echo ""

# Проверка портов
echo -e "${BLUE}🔌 Проверка портов:${NC}"
if command -v ss &> /dev/null; then
    if ss -tuln | grep -q ":8000"; then
        echo -e "   ⚠️  Порт 8000 уже занят:"
        ss -tuln | grep ":8000" | sed 's/^/      /'
    else
        echo -e "   ✅ Порт 8000 свободен"
    fi
else
    echo -e "   ⚠️  ss команда не найдена, проверка портов пропущена"
fi
echo ""

# Проверка прав
echo -e "${BLUE}🔐 Проверка прав:${NC}"
if [ "$EUID" -eq 0 ]; then
    echo -e "   ✅ Скрипт запущен с правами root"
else
    echo -e "   ⚠️  Скрипт запущен без прав root"
    echo -e "   💡 Для установки используйте: sudo ./setup-autostart.sh"
fi
echo ""

# Проверка системных служб
echo -e "${BLUE}⚙️  Проверка системных служб:${NC}"
if command -v systemctl &> /dev/null; then
    echo -e "   ✅ systemd доступен"
    
    if systemctl is-active --quiet qresos-backend 2>/dev/null; then
        echo -e "   ⚠️  Сервис qresos-backend уже запущен"
    else
        echo -e "   ✅ Сервис qresos-backend не запущен"
    fi
else
    echo -e "   ❌ systemd не найден"
fi
echo ""

# Проверка места на диске
echo -e "${BLUE}💾 Проверка места на диске:${NC}"
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
if [ "$AVAILABLE_SPACE" -gt 1048576 ]; then  # 1GB в KB
    echo -e "   ✅ Достаточно места на диске ($(($AVAILABLE_SPACE / 1024))MB свободно)"
else
    echo -e "   ⚠️  Мало места на диске ($(($AVAILABLE_SPACE / 1024))MB свободно)"
    echo -e "   💡 Рекомендуется освободить место"
fi
echo ""

# Итоговые рекомендации
echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}📋 Рекомендации для установки:${NC}"
echo -e "${BLUE}==================================================${NC}"

# Проверка готовности к установке
READY=true

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Установите Python3: sudo apt update && sudo apt install python3 python3-pip python3-venv${NC}"
    READY=false
fi

if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Запустите установку с правами root: sudo ./setup-autostart.sh${NC}"
fi

if [ "$READY" = true ]; then
    echo -e "${GREEN}✅ Система готова к установке QRes OS 4${NC}"
    echo -e "${GREEN}🚀 Запустите: sudo ./setup-autostart.sh${NC}"
else
    echo -e "${RED}❌ Система не готова. Устраните указанные проблемы.${NC}"
fi

echo ""
