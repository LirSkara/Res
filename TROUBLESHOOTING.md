# 🛠️ Устранение проблем QRes OS 4

## 🚨 Частые проблемы при установке

### 1. Ошибка "externally-managed-environment"

**Проблема:** Python 3.12+ защищает системные пакеты

**Решения:**

```bash
# Вариант 1: Установка python3-venv
sudo apt update
sudo apt install python3-full python3-venv python3-pip

# Вариант 2: Использование pipx
sudo apt install pipx
pipx install fastapi uvicorn

# Вариант 3: Принудительная установка (не рекомендуется)
pip install --break-system-packages -r requirements.txt
```

### 2. Ошибка создания директории

**Проблема:** Недостаточно прав или директория не создается

**Решение:**

```bash
# Создание директории вручную
sudo mkdir -p /home/admin/qresos/backend
sudo chown -R admin:admin /home/admin/qresos

# Проверка прав
ls -la /home/admin/
```

### 3. Ошибка "Can't assign requested address"

**Проблема:** IP 192.168.4.1 не настроен на сетевом интерфейсе

**Решения:**

```bash
# Для разработки - используйте
./start-dev.sh

# Для продакшена - настройте сеть
sudo ./check-system.sh
# Следуйте инструкциям в NETWORK_SETUP.md
```

### 4. Ошибка установки зависимостей

**Проблема:** Не удается установить Python пакеты

**Решения:**

```bash
# Обновление системы
sudo apt update && sudo apt upgrade

# Установка минимальных зависимостей
pip install -r requirements-minimal.txt

# Ручная установка основных пакетов
pip install fastapi uvicorn sqlalchemy alembic aiosqlite
```

### 5. Service файл не найден

**Проблема:** Отсутствует qresos-backend.service

**Решение:** Скрипт setup-autostart.sh теперь создает его автоматически

```bash
# Проверка после установки
sudo systemctl status qresos-backend
```

### 6. Планшеты не могут подключиться к серверу

**Проблема:** Планшеты подключены к WiFi, но не видят сервер

**Решения:**

```bash
# Проверка CORS настроек
curl http://192.168.4.1:8000/debug/cors

# Проверка файрвола
sudo ufw status
sudo ufw allow 8000/tcp

# Проверка подключенных устройств
arp -a | grep "192.168.4"

# Перезапуск WiFi сервисов
sudo systemctl restart hostapd dnsmasq
```

### 7. WiFi точка доступа не работает

**Проблема:** Планшеты не видят WiFi сеть

**Решения:**

```bash
# Проверка hostapd
sudo systemctl status hostapd
sudo journalctl -u hostapd -f

# Проверка конфигурации
sudo hostapd -dd /etc/hostapd/hostapd.conf

# Проверка интерфейса
iwconfig wlan0
ip addr show wlan0

# Перезапуск WiFi
sudo systemctl restart hostapd
```

## 🔧 Диагностика

### Проверка системы

```bash
# Полная проверка
./check-system.sh

# Проверка Python
python3 --version
python3 -m venv --help
pip3 --version

# Проверка сети
ip addr show
ss -tuln | grep :8000
```

### Проверка установки

```bash
# Статус сервиса
sudo systemctl status qresos-backend

# Логи сервиса
sudo journalctl -u qresos-backend -f

# Проверка файлов
ls -la /home/admin/qresos/backend/
ls -la /etc/systemd/system/qresos-backend.service
```

### Проверка сети

```bash
# Доступные IP адреса
hostname -I

# Проверка конкретного IP
ip addr show | grep 192.168.4.1

# Тест подключения с сервера
curl http://192.168.4.1:8000/docs
curl http://127.0.0.1:8000/docs

# Проверка подключенных планшетов
arp -a | grep "192.168.4"

# Проверка DHCP аренд
cat /var/lib/dhcp/dhcpcd.leases 2>/dev/null || echo "DHCP leases file not found"
```

### Проверка WiFi точки доступа

```bash
# Статус WiFi AP
sudo systemctl status hostapd

# Статус DHCP сервера  
sudo systemctl status dnsmasq

# Проверка WiFi интерфейса
iwconfig wlan0

# Проверка активных подключений
sudo iw dev wlan0 station dump
```

## 🏥 Восстановление

### Полная переустановка

```bash
# Остановка сервиса
sudo systemctl stop qresos-backend
sudo systemctl disable qresos-backend

# Удаление файлов
sudo rm -rf /home/admin/qresos
sudo rm -f /etc/systemd/system/qresos-backend.service
sudo rm -f /usr/local/bin/qresos-control

# Перезагрузка systemd
sudo systemctl daemon-reload

# Новая установка
sudo ./setup-autostart.sh
```

### Сброс базы данных

```bash
# Остановка сервиса
sudo systemctl stop qresos-backend

# Удаление базы данных
sudo rm -f /home/admin/qresos/backend/app.db

# Применение миграций заново
cd /home/admin/qresos/backend
sudo -u admin bash -c "source venv/bin/activate && python3 -m alembic upgrade head"

# Запуск сервиса
sudo systemctl start qresos-backend
```

## 📚 Полезные команды

### Управление сервисом

```bash
# Статус
sudo qresos-control status
sudo systemctl status qresos-backend

# Запуск/остановка
sudo qresos-control start
sudo qresos-control stop
sudo qresos-control restart

# Логи
sudo qresos-control logs
sudo journalctl -u qresos-backend --since "1 hour ago"
```

### Работа с базой данных

```bash
# Просмотр таблиц (SQLite)
sudo -u admin sqlite3 /home/admin/qresos/backend/app.db ".tables"

# Создание бэкапа
sudo qresos-control backup

# Миграции
sudo qresos-control migrate
```

### Мониторинг

```bash
# Использование ресурсов
top -p $(pgrep -f qresos)
ps aux | grep qresos

# Сетевые подключения
sudo ss -tulpn | grep :8000
sudo lsof -i :8000

# Место на диске
df -h /home/admin/qresos
du -sh /home/admin/qresos
```

## 🆘 Получение помощи

Если проблема не решается:

1. Запустите диагностику:
   ```bash
   ./check-system.sh > system-check.log
   sudo qresos-control status > service-status.log
   ```

2. Соберите логи:
   ```bash
   sudo journalctl -u qresos-backend > service.log
   dmesg | tail -50 > dmesg.log
   ```

3. Проверьте конфигурацию:
   ```bash
   cat /home/admin/qresos/backend/.env
   cat /etc/systemd/system/qresos-backend.service
   ```

4. Опишите проблему с приложением собранной информации.
