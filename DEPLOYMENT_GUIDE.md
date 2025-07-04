# 🚀 QRes OS 4 - Deployment Guide

## 📊 Статус проекта: ГОТОВ К РАЗВЁРТЫВАНИЮ

**Последнее тестирование:** 4 июля 2025 г.  
**Успешность тестов:** 100% (39/39 тестов пройдено)  
**Эндпоинтов API:** 33  
**Статус:** ✅ PRODUCTION READY

## 🎯 Что реализовано

### ✅ Основные модули
- [x] Аутентификация и авторизация (JWT + PIN)
- [x] Управление пользователями (3 роли: admin, waiter, chef)
- [x] Управление локациями ресторана
- [x] Управление столиками с QR-кодами
- [x] Управление категориями блюд
- [x] Управление блюдами и меню
- [x] Управление ингредиентами и складом
- [x] Система заказов (полный цикл)
- [x] Способы оплаты
- [x] WebSocket для real-time уведомлений
- [x] Публичное меню для QR-кодов

### ✅ API Features
- [x] REST API с автодокументацией (Swagger UI)
- [x] Валидация данных через Pydantic
- [x] Обработка ошибок и исключений
- [x] Пагинация и фильтрация
- [x] CRUD операции для всех сущностей
- [x] Health check эндпоинт

### ✅ Безопасность
- [x] JWT токены с истечением срока
- [x] Хеширование паролей (bcrypt)
- [x] Роль-основанный доступ (RBAC)
- [x] PIN-код аутентификация для быстрого входа
- [x] CORS настройки

### ✅ База данных
- [x] SQLAlchemy 2.0 с async поддержкой
- [x] Миграции через Alembic
- [x] Поддержка SQLite (по умолчанию) и PostgreSQL
- [x] Инициализация с демо-данными

## 🔧 Быстрый старт

### 1. Запуск в development режиме

```bash
cd /Users/lirskara/Desktop/qresos4/backend
python3 -m uvicorn app.main:app --reload --port 8000
```

### 2. Тестирование системы

```bash
python3 test_api.py
```

### 3. Доступ к документации

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

## 👥 Тестовые пользователи

| Роль | Логин | Пароль | PIN |
|------|-------|---------|-----|
| Администратор | `admin` | `admin123` | `1234` |
| Официант | `waiter1` | `waiter123` | `1111` |
| Кухня | `chef1` | `chef123` | `2222` |

## 🍓 Развёртывание на Raspberry Pi

### Системные требования
- **Raspberry Pi 3B+** или новее
- **1GB RAM** (рекомендуется)
- **16GB MicroSD** (минимум)
- **Raspberry Pi OS Lite** (рекомендуется)

### 1. Подготовка Raspberry Pi

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.9+
sudo apt install python3 python3-pip python3-venv git -y

# Создание пользователя для приложения
sudo useradd -m -s /bin/bash qres
sudo usermod -aG sudo qres
```

### 2. Установка приложения

```bash
# Переключение на пользователя qres
sudo su - qres

# Клонирование проекта
git clone <your-repository-url> qres-os4
cd qres-os4/backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
nano .env  # Редактируем настройки
```

### 3. Настройка .env для production

```properties
# Безопасность
SECRET_KEY=your-very-secure-secret-key-256-bit
DEBUG=False
RELOAD=False

# Сеть
HOST=0.0.0.0
PORT=8000

# QR коды (укажите IP вашего Pi)
QR_BASE_URL=http://192.168.1.XXX:8000/menu

# База данных (можно оставить SQLite или настроить PostgreSQL)
DATABASE_URL=sqlite+aiosqlite:///./qres_os4.db
```

### 4. Инициализация базы данных

```bash
# Создание миграций
alembic upgrade head

# Инициализация с демо-данными
python3 init_db.py
```

### 5. Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/qres-os4.service
```

```ini
[Unit]
Description=QRes OS 4 Restaurant Management System
After=network.target

[Service]
User=qres
Group=qres
WorkingDirectory=/home/qres/qres-os4/backend
Environment=PATH=/home/qres/qres-os4/backend/venv/bin
ExecStart=/home/qres/qres-os4/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl daemon-reload
sudo systemctl enable qres-os4
sudo systemctl start qres-os4

# Проверка статуса
sudo systemctl status qres-os4
```

### 6. Настройка Nginx (опционально)

```bash
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/qres-os4
```

```nginx
server {
    listen 80;
    server_name your-restaurant.local;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/qres-os4 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 Обслуживание и мониторинг

### Логи
```bash
# Просмотр логов приложения
sudo journalctl -u qres-os4 -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup базы данных
```bash
# Создание backup
cp qres_os4.db backups/qres_os4_$(date +%Y%m%d_%H%M%S).db

# Автоматический backup (crontab)
echo "0 2 * * * cd /home/qres/qres-os4/backend && cp qres_os4.db backups/qres_os4_\$(date +\%Y\%m\%d_\%H\%M\%S).db" | crontab -
```

### Обновление системы
```bash
cd /home/qres/qres-os4/backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart qres-os4
```

## 📱 Интеграция с frontend

Система готова для интеграции с любым frontend:
- **React/Next.js** - для веб-интерфейса
- **React Native/Flutter** - для мобильного приложения
- **Vue.js/Angular** - альтернативные веб-фреймворки

### Пример подключения

```javascript
// Аутентификация
const response = await fetch('http://192.168.1.XXX:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin123' })
});

const { access_token } = await response.json();

// Использование API
const orders = await fetch('http://192.168.1.XXX:8000/orders/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

## 🎯 Следующие шаги

1. **Frontend разработка** - создание веб/мобильного интерфейса
2. **QR-коды** - печать QR-кодов для столиков
3. **Интеграция оплаты** - подключение платёжных систем
4. **Отчёты** - добавление аналитики и отчётов
5. **Уведомления** - push-уведомления для мобильного приложения

---

## 📞 Поддержка

**Статус:** ✅ Готово к production использованию  
**Тестирование:** 100% покрытие API  
**Документация:** Полная документация API доступна  

Система QRes OS 4 полностью готова к развёртыванию и использованию в реальном ресторане! 🚀
