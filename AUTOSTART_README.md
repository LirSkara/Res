# QRes OS 4 - Автостарт для Ubuntu Server 24

Этот набор скриптов позволяет настроить автоматический запуск QRes OS 4 на Ubuntu Server 24 LTS.

## 📋 Содержимое

- `qresos-backend.service` - systemd service файл
- `setup-autostart.sh` - скрипт установки и настройки автостарта
- `manage-service.sh` - скрипт управления сервисом
- `AUTOSTART_README.md` - этот файл с инструкциями

## 🚀 Быстрая установка

1. **Скопируйте проект на сервер:**
   ```bash
   # Загрузите проект в любую директорию, например:
   git clone <ваш-репозиторий> /tmp/qresos4
   cd /tmp/qresos4/backend
   ```

2. **Сделайте скрипты исполняемыми:**
   ```bash
   chmod +x setup-autostart.sh
   chmod +x manage-service.sh
   chmod +x start.sh
   chmod +x stop.sh
   ```

3. **Запустите установку:**
   ```bash
   sudo ./setup-autostart.sh
   ```

## 📁 Структура после установки

После установки ваш проект будет размещен в следующей структуре:

```
/var/www/qresos4/
├── backend/           # Основной проект
│   ├── app/          # FastAPI приложение
│   ├── venv/         # Виртуальное окружение Python
│   ├── .env          # Конфигурация (создается автоматически)
│   ├── start.sh      # Скрипт запуска
│   └── ...
└── ...

/var/log/qresos4/     # Логи приложения

/etc/systemd/system/
└── qresos-backend.service  # Systemd service файл
```

## 🔧 Управление сервисом

После установки используйте скрипт `manage-service.sh` для управления:

```bash
# Показать статус
./manage-service.sh status

# Запустить сервис
./manage-service.sh start

# Остановить сервис
./manage-service.sh stop

# Перезапустить сервис
./manage-service.sh restart

# Посмотреть логи в реальном времени
./manage-service.sh logs

# Включить автостарт
./manage-service.sh enable

# Отключить автостарт
./manage-service.sh disable
```

## 🔧 Системные команды

Также можно использовать стандартные команды systemd:

```bash
# Статус сервиса
sudo systemctl status qresos-backend

# Запуск/остановка/перезапуск
sudo systemctl start qresos-backend
sudo systemctl stop qresos-backend
sudo systemctl restart qresos-backend

# Автостарт
sudo systemctl enable qresos-backend   # включить
sudo systemctl disable qresos-backend  # отключить

# Логи
sudo journalctl -u qresos-backend -f   # в реальном времени
sudo journalctl -u qresos-backend      # все логи
```

## ⚙️ Конфигурация

### Переменные окружения

Файл `.env` создается автоматически со следующими настройками:

```bash
DEBUG=false
RELOAD=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=<автоматически-сгенерированный>
LOG_DIR=/var/log/qresos4
```

### Настройка порта

Чтобы изменить порт по умолчанию (8000):

1. Отредактируйте `.env` файл:
   ```bash
   sudo nano /var/www/qresos4/backend/.env
   ```

2. Измените значение PORT:
   ```bash
   PORT=3000
   ```

3. Перезапустите сервис:
   ```bash
   sudo systemctl restart qresos-backend
   ```

### Настройка базы данных

По умолчанию используется SQLite. Для PostgreSQL:

1. Установите PostgreSQL:
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. Создайте базу данных и пользователя:
   ```bash
   sudo -u postgres psql
   CREATE DATABASE qresos4;
   CREATE USER qresos WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE qresos4 TO qresos;
   \q
   ```

3. Обновите DATABASE_URL в `.env`:
   ```bash
   DATABASE_URL=postgresql://qresos:your_password@localhost/qresos4
   ```

4. Перезапустите сервис:
   ```bash
   sudo systemctl restart qresos-backend
   ```

## 🔍 Диагностика

### Проверка работы сервиса

```bash
# Проверка статуса
curl http://localhost:8000/
curl http://localhost:8000/docs

# Проверка процессов
ps aux | grep uvicorn
netstat -tlnp | grep :8000
```

### Общие проблемы

1. **Сервис не запускается:**
   ```bash
   # Проверьте логи
   sudo journalctl -u qresos-backend -n 50
   
   # Проверьте права доступа
   ls -la /var/www/qresos4/backend/
   ```

2. **Порт занят:**
   ```bash
   # Найдите процесс, использующий порт
   sudo lsof -i :8000
   
   # Остановите конфликтующий процесс или измените порт
   ```

3. **Проблемы с базой данных:**
   ```bash
   # Проверьте миграции
   cd /var/www/qresos4/backend
   source venv/bin/activate
   python -m alembic current
   python -m alembic upgrade head
   ```

## 🛡️ Безопасность

### Пользователь сервиса

Сервис запускается от имени пользователя `qresos` (не root) для повышения безопасности.

### Файрвол

Настройте UFW для ограничения доступа:

```bash
# Разрешить только необходимые порты
sudo ufw allow ssh
sudo ufw allow 8000/tcp
sudo ufw enable
```

### SSL/HTTPS

Для production рекомендуется использовать обратный прокси (nginx) с SSL:

```bash
# Установка nginx
sudo apt install nginx

# Базовая конфигурация nginx
sudo nano /etc/nginx/sites-available/qresos4
```

## 📊 Мониторинг

### Логи

Логи сервиса доступны через journalctl:

```bash
# Логи сервиса в реальном времени
sudo journalctl -u qresos-backend -f

# Логи за последний час
sudo journalctl -u qresos-backend --since "1 hour ago"

# Логи приложения
tail -f /var/log/qresos4/app.log
```

### Ресурсы

Мониторинг использования ресурсов:

```bash
# CPU и память
top -p $(pgrep -f "uvicorn app.main:app")

# Дисковое пространство
df -h /var/www/qresos4/
```

## 🔄 Обновление

Для обновления проекта:

1. Остановите сервис:
   ```bash
   sudo systemctl stop qresos-backend
   ```

2. Обновите файлы проекта в `/var/www/qresos4/backend/`

3. Обновите зависимости:
   ```bash
   cd /var/www/qresos4/backend
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Примените миграции:
   ```bash
   python -m alembic upgrade head
   ```

5. Запустите сервис:
   ```bash
   sudo systemctl start qresos-backend
   ```

## 🗑️ Удаление

Для полного удаления:

```bash
# Остановить и удалить сервис
./manage-service.sh uninstall

# Удалить файлы проекта
sudo rm -rf /var/www/qresos4

# Удалить логи
sudo rm -rf /var/log/qresos4

# Удалить пользователя (опционально)
sudo userdel qresos
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u qresos-backend`
2. Убедитесь, что все зависимости установлены
3. Проверьте права доступа к файлам
4. Убедитесь, что порт не занят другим процессом

---

**QRes OS 4** - Система управления рестораном  
Версия: 4.0  
Совместимость: Ubuntu Server 24 LTS
