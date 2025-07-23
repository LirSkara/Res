# Устранение проблем автостарта QRes OS 4

## 🔧 Частые проблемы и их решения

### 1. Сервис не запускается

**Проблема:** `sudo systemctl status qresos-backend` показывает failed

**Решения:**

```bash
# Проверьте логи сервиса
sudo journalctl -u qresos-backend -n 50

# Проверьте права доступа
ls -la /home/admin/qresos/backend/start.sh

# Убедитесь что Python доступен
which python3

# Проверьте виртуальное окружение
cd /home/admin/qresos/backend
source venv/bin/activate
python3 -c "import app.main"
```

### 2. Ошибка "Permission denied"

**Проблема:** Нет прав доступа к файлам проекта

**Решение:**
```bash
# Установите правильные права
sudo chown -R admin:admin /home/admin/qresos/backend
sudo chmod +x /home/admin/qresos/backend/start.sh

# Если проект не в домашней директории admin
sudo chmod -R 755 /path/to/your/project
```

### 3. Ошибка "Module not found"

**Проблема:** Python не может найти модули

**Решение:**
```bash
# Переустановите зависимости
cd /home/admin/qresos/backend
source venv/bin/activate
pip install -r requirements.txt

# Если не помогает, пересоздайте виртуальное окружение
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Ошибка базы данных

**Проблема:** Не удается подключиться к базе данных

**Решение:**
```bash
# Примените миграции
cd /home/admin/qresos/backend
source venv/bin/activate
python3 -m alembic upgrade head

# Проверьте файл базы данных
ls -la app.db
```

### 5. Порт уже занят

**Проблема:** `Address already in use`

**Решение:**
```bash
# Найдите процесс на порту 8000
sudo lsof -i :8000

# Остановите конфликтующий процесс
sudo kill -9 [PID]

# Или измените порт в .env
nano /home/admin/qresos/backend/.env
# PORT=8001
```

### 6. Автостарт не работает после перезагрузки

**Проблема:** Сервис не запускается автоматически

**Решение:**
```bash
# Убедитесь что автостарт включен
sudo systemctl enable qresos-backend

# Проверьте статус
sudo systemctl is-enabled qresos-backend

# Перезагрузите systemd
sudo systemctl daemon-reload
```

## 🔍 Диагностические команды

### Полная проверка системы
```bash
# Статус сервиса
sudo systemctl status qresos-backend

# Логи сервиса
sudo journalctl -u qresos-backend -f

# Проверка сети
curl -f http://localhost:8000/ || echo "API недоступен"

# Проверка файлов
ls -la /home/admin/qresos/backend/

# Проверка Python окружения
cd /home/admin/qresos/backend
source venv/bin/activate
python3 -c "import sys; print(f'Python: {sys.executable}')"
python3 -c "import app.main; print('App imports OK')"
```

### Ручной запуск для отладки
```bash
# Остановите сервис
sudo systemctl stop qresos-backend

# Запустите вручную
cd /home/admin/qresos/backend
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🔄 Переустановка

Если ничего не помогает, переустановите сервис:

```bash
# Остановите и удалите сервис
sudo systemctl stop qresos-backend
sudo systemctl disable qresos-backend
sudo rm /etc/systemd/system/qresos-backend.service
sudo systemctl daemon-reload

# Запустите установку заново
cd /path/to/your/project/backend
sudo ./setup-autostart.sh
```

## 📞 Дополнительная помощь

Если проблема не решается:

1. Соберите диагностическую информацию:
```bash
# Создайте файл с диагностикой
{
    echo "=== SYSTEM INFO ==="
    uname -a
    echo "=== SERVICE STATUS ==="
    sudo systemctl status qresos-backend
    echo "=== RECENT LOGS ==="
    sudo journalctl -u qresos-backend -n 20
    echo "=== ENVIRONMENT ==="
    cd /home/admin/qresos/backend && cat .env
    echo "=== PYTHON VERSION ==="
    python3 --version
    echo "=== NETWORK ==="
    ip addr show
} > qresos-diagnostic.txt
```

2. Проверьте файл `qresos-diagnostic.txt` и используйте его для поиска решения.

---

**Совет:** Всегда проверяйте логи первым делом - они содержат наиболее точную информацию о проблеме.
