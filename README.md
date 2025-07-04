# 🍽️ QRes OS 4 - Restaurant Management System

> Современная система управления рестораном нового поколения

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776ab.svg?style=flat&logo=python)](https://www.python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00.svg?style=flat&logo=sqlalchemy)](https://www.sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

QRes OS 4 — это полнофункциональная система управления рестораном, построенная на современном стеке технологий с упором на производительность, масштабируемость и удобство использования. Система предназначена для автоматизации всех процессов ресторана: от управления меню и заказами до аналитики и отчетности.

## ✨ Основные возможности

### 🎯 Для администраторов
- **Управление персоналом** — создание пользователей, назначение ролей, PIN-коды
- **Настройка ресторана** — локации, столики, категории блюд
- **Гибкое меню** — блюда с вариациями (размеры, цены), ингредиенты
- **Аналитика** — отчеты по продажам, популярные блюда, эффективность персонала
- **Системные настройки** — способы оплаты, конфигурация, бэкапы

### 👨‍🍳 Для персонала кухни
- **Real-time заказы** — мгновенные уведомления о новых заказах
- **Управление статусами** — принятие, приготовление, готовность блюд
- **Время приготовления** — отслеживание и оптимизация процессов
- **Специальные требования** — обработка комментариев к блюдам

### 👨‍💼 Для официантов
- **Быстрый вход по PIN** — моментальная авторизация
- **Управление столиками** — статусы занятости, QR-коды
- **Заказы** — создание, изменение, отслеживание статуса
- **Расчеты** — обработка оплаты, различные способы платежа

### 📱 Для клиентов
- **QR-меню** — сканирование QR-кода столика для просмотра меню
- **Онлайн заказы** — возможность самостоятельного оформления
- **Актуальная информация** — доступность блюд, время приготовления

## 🏗️ Архитектура системы

```
qresos4/backend/
├── 📁 app/                     # Основное приложение
│   ├── 📄 main.py             # Точка входа FastAPI
│   ├── 📄 config.py           # Конфигурация
│   ├── 📄 database.py         # База данных
│   ├── 📄 deps.py             # Зависимости
│   │
│   ├── 📁 models/             # SQLAlchemy модели
│   │   ├── 👤 user.py         # Пользователи и роли
│   │   ├── 📍 location.py     # Зоны ресторана
│   │   ├── 🪑 table.py        # Столики
│   │   ├── 📂 category.py     # Категории блюд
│   │   ├── 🍽️ dish.py         # Блюда
│   │   ├── 🔄 dish_variation.py # Вариации блюд
│   │   ├── 📦 ingredient.py   # Ингредиенты
│   │   ├── 📝 order.py        # Заказы
│   │   ├── 📋 order_item.py   # Позиции заказов
│   │   └── 💳 paymentmethod.py # Способы оплаты
│   │
│   ├── 📁 schemas/            # Pydantic схемы валидации
│   │   ├── 👤 user.py         # Схемы пользователей
│   │   ├── 🪑 table.py        # Схемы столиков
│   │   ├── 🍽️ dish.py         # Схемы блюд
│   │   ├── 📝 order.py        # Схемы заказов
│   │   ├── 📄 common.py       # Общие схемы
│   │   └── ...                # Остальные схемы
│   │
│   ├── 📁 routers/            # FastAPI роутеры
│   │   ├── 🔐 auth.py         # Аутентификация
│   │   ├── 👥 users.py        # Управление пользователями
│   │   ├── 🪑 tables.py       # Управление столиками
│   │   ├── 🍽️ dishes.py       # Управление блюдами
│   │   ├── 📝 orders.py       # Управление заказами
│   │   ├── 🔌 websocket.py    # WebSocket соединения
│   │   └── ...                # Остальные роутеры
│   │
│   └── 📁 services/           # Бизнес-логика
│       ├── 🔐 auth.py         # Сервисы аутентификации
│       ├── 🍽️ dishes.py       # Сервисы блюд
│       ├── 📝 orders.py       # Сервисы заказов
│       └── 🛠️ utils.py        # Утилиты
│
├── 📁 alembic/                # Миграции базы данных
├── 📁 tests/                  # Тесты
├── 📁 docs/                   # Документация
├── 📁 uploads/                # Загруженные файлы
├── 📄 requirements.txt        # Зависимости Python
├── 📄 alembic.ini            # Конфигурация миграций
└── 📄 app.db                 # База данных SQLite
```

## 🚀 Технологический стек

### Backend
- **FastAPI** — современный веб-фреймворк для Python
- **SQLAlchemy 2.0** — ORM с поддержкой async/await
- **Alembic** — миграции базы данных
- **Pydantic** — валидация данных и сериализация
- **JWT** — аутентификация и авторизация
- **WebSocket** — real-time коммуникация

### База данных
- **SQLite** (по умолчанию) — для разработки и небольших установок
- **PostgreSQL** — для production среды
- **Async поддержка** — неблокирующие операции с БД

### Безопасность
- **Bcrypt** — хеширование паролей
- **JWT токены** — безопасная аутентификация
- **CORS** — настраиваемая политика доступа
- **Роли пользователей** — гранулярные права доступа

## 🛠️ Установка и запуск

### Системные требования
- **Python 3.9+**
- **512MB RAM** (минимум для Raspberry Pi)
- **SQLite/PostgreSQL**

### Быстрый старт

1. **Клонирование репозитория**
```bash
git clone <repository-url>
cd qresos4/backend
```

2. **Создание виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows
```

3. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

4. **Настройка окружения**
```bash
cp .env.example .env
# Отредактируйте .env под ваши нужды
```

5. **Инициализация базы данных**
```bash
python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
print('✅ База данных инициализирована!')
"
```

6. **Запуск сервера**
```bash
# Режим разработки
uvicorn app.main:app --reload

# Production режим
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 🐳 Запуск с Docker (опционально)

```bash
# Сборка образа
docker build -t qresos4 .

# Запуск контейнера
docker run -p 8000:8000 qresos4
```

## ⚙️ Конфигурация

### Основные настройки (.env)

```env
# База данных
DATABASE_URL=sqlite+aiosqlite:///./app.db
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/qresos4

# Безопасность
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Сервер
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS (для фронтенда)
CORS_ORIGINS=["http://localhost:3000","http://192.168.1.*"]

# QR-коды
QR_BASE_URL=http://192.168.1.100:8000/menu

# Ресторан
RESTAURANT_NAME="QRes OS 4 Restaurant"
RESTAURANT_TIMEZONE="Europe/Moscow"
```

## 📱 API Документация

После запуска сервера документация доступна по адресам:

- **🔍 Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **📚 ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **🔧 Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### Полный список API эндпоинтов

#### 🔐 Аутентификация (`/auth`)
```http
POST   /auth/login          # Вход по логину/паролю
POST   /auth/login/pin      # Быстрый вход по PIN-коду
GET    /auth/me             # Информация о текущем пользователе
POST   /auth/logout         # Выход из системы
```

#### 👥 Управление пользователями (`/users`) — *Только для администраторов*
```http
GET    /users/              # Список пользователей с фильтрацией
POST   /users/              # Создание нового пользователя
GET    /users/{user_id}     # Получение пользователя по ID
PATCH  /users/{user_id}     # Обновление данных пользователя
PATCH  /users/{user_id}/password  # Смена пароля пользователя
DELETE /users/{user_id}     # Удаление пользователя
```

#### 🏢 Локации (`/locations`)
```http
GET    /locations/          # Список локаций/зон ресторана
POST   /locations/          # Создание новой локации (админ)
GET    /locations/{location_id}     # Получение локации с количеством столиков
PATCH  /locations/{location_id}     # Обновление локации (админ)
GET    /locations/{location_id}/tables  # Столики в конкретной локации
DELETE /locations/{location_id}     # Удаление локации (админ)
```

#### 🪑 Столики (`/tables`)
```http
GET    /tables/             # Список столиков с фильтрацией
POST   /tables/             # Создание нового столика (админ)
GET    /tables/{table_id}   # Получение информации о столике
PATCH  /tables/{table_id}   # Обновление данных столика (админ)
PATCH  /tables/{table_id}/status    # Изменение статуса занятости (официант)
GET    /tables/{table_id}/qr        # Получение QR-кода столика
DELETE /tables/{table_id}   # Удаление столика (админ)
```

#### 📂 Категории блюд (`/categories`)
```http
GET    /categories/         # Список категорий с фильтрацией
POST   /categories/         # Создание новой категории (админ)
GET    /categories/{category_id}     # Получение категории с блюдами
PATCH  /categories/{category_id}     # Обновление категории (админ)
GET    /categories/{category_id}/dishes  # Блюда в категории
DELETE /categories/{category_id}     # Удаление категории (админ)
```

#### 🍽️ Блюда (`/dishes`)
```http
GET    /dishes/             # Список всех блюд с фильтрацией
GET    /dishes/menu         # Публичное меню для клиентов
POST   /dishes/             # Создание нового блюда (админ)
GET    /dishes/{dish_id}    # Получение блюда с информацией о категории
PATCH  /dishes/{dish_id}    # Обновление данных блюда (админ)
PATCH  /dishes/{dish_id}/availability   # Изменение доступности блюда
DELETE /dishes/{dish_id}    # Удаление блюда (админ)

# Вариации блюд
GET    /dishes/{dish_id}/variations/    # Список вариаций блюда
POST   /dishes/{dish_id}/variations/    # Создание новой вариации (админ)
GET    /dishes/{dish_id}/variations/{variation_id}       # Получение конкретной вариации
PATCH  /dishes/{dish_id}/variations/{variation_id}       # Обновление вариации (админ)
PATCH  /dishes/{dish_id}/variations/{variation_id}/availability  # Изменение доступности вариации
DELETE /dishes/{dish_id}/variations/{variation_id}       # Удаление вариации (админ)
```

#### 📝 Заказы (`/orders`)
```http
GET    /orders/             # Список заказов с фильтрацией по статусам
POST   /orders/             # Создание нового заказа
GET    /orders/{order_id}   # Получение заказа с полной детализацией
PATCH  /orders/{order_id}/status    # Обновление статуса заказа (кухня/официант)
PATCH  /orders/{order_id}/payment   # Обновление статуса оплаты (официант)
GET    /orders/stats/summary         # Статистика заказов (менеджер/админ)
DELETE /orders/{order_id}   # Отмена заказа (официант/админ)

# Позиции заказов
POST   /orders/{order_id}/items/     # Добавление блюда в заказ
PATCH  /orders/{order_id}/items/{item_id}        # Обновление позиции заказа
PATCH  /orders/{order_id}/items/{item_id}/status # Изменение статуса позиции (кухня)
DELETE /orders/{order_id}/items/{item_id}        # Удаление позиции из заказа
```

#### 📦 Ингредиенты (`/ingredients`)
```http
GET    /ingredients/        # Список ингредиентов с фильтрацией
POST   /ingredients/        # Создание нового ингредиента (админ)
GET    /ingredients/{ingredient_id}  # Получение ингредиента по ID
PATCH  /ingredients/{ingredient_id}  # Обновление ингредиента (админ)
GET    /ingredients/allergens/list   # Список всех аллергенов
DELETE /ingredients/{ingredient_id}  # Удаление ингредиента (админ)
```

#### � Способы оплаты (`/payment-methods`)
```http
GET    /payment-methods/    # Список способов оплаты
GET    /payment-methods/active      # Только активные способы оплаты
POST   /payment-methods/    # Создание способа оплаты (админ)
GET    /payment-methods/{payment_method_id}    # Получение способа оплаты
PATCH  /payment-methods/{payment_method_id}    # Обновление способа оплаты (админ)
DELETE /payment-methods/{payment_method_id}    # Удаление способа оплаты (админ)
```

#### �🔌 WebSocket (`/ws`)
```websocket
WS     /ws/orders           # Real-time уведомления о заказах
```

### 📋 Примеры запросов

#### Создание заказа
```bash
curl -X POST "http://localhost:8000/orders/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "table_id": 1,
    "order_type": "DINE_IN",
    "items": [
      {
        "dish_id": 1,
        "dish_variation_id": 2,
        "quantity": 2,
        "comment": "Без лука"
      }
    ],
    "notes": "Срочный заказ"
  }'
```

#### Получение публичного меню
```bash
curl "http://localhost:8000/dishes/menu"
```

#### Обновление статуса заказа
```bash
curl -X PATCH "http://localhost:8000/orders/1/status" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
```

#### WebSocket подключение (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/orders?token=YOUR_TOKEN');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Новое событие:', data.type, data);
};
```

## 🆕 Инновационная система блюд

### Гибкие вариации
QRes OS 4 поддерживает революционную систему вариаций блюд:

```
🍕 Пицца "Маргарита"
├── 🥧 Маленькая (25см) — 450₽
├── 🍕 Средняя (30см)   — 650₽
└── 🍕 Большая (35см)   — 850₽

🥤 Кока-Кола
├── 🥃 0.33л — 150₽
├── 🥤 0.5л  — 200₽
└── 🧊 1л    — 350₽
```

### Преимущества
- ✅ **Гибкое ценообразование** — разные цены для разных размеров
- ✅ **Индивидуальное управление** — отключение конкретных вариаций
- ✅ **Простота заказа** — клиенты легко выбирают нужный размер
- ✅ **Аналитика** — статистика по популярности вариаций

## 🔐 Система ролей и безопасность

### Роли пользователей
- 👨‍💼 **Admin** — полный доступ ко всем функциям
- 👨‍🍳 **Kitchen** — управление заказами и статусами блюд
- 🧑‍💼 **Waiter** — создание заказов, управление столиками
- 📊 **Manager** — просмотр отчетов и аналитики

### Аутентификация
- 🔑 **JWT токены** — безопасная авторизация
- 📱 **PIN-коды** — быстрый вход для персонала
- 🔒 **Хеширование паролей** — bcrypt защита
- ⏰ **Сессии** — настраиваемое время жизни токенов

## 🌐 Real-time функции

### WebSocket уведомления
```javascript
// Подключение к WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/orders');

// Обработка событий
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'order_created':
            showNewOrderNotification(data.order);
            break;
        case 'order_status_changed':
            updateOrderStatus(data.order_id, data.status);
            break;
    }
};
```

### События системы
- 🔔 **Новый заказ** — уведомление кухни
- 🍳 **Блюдо готово** — уведомление официанта
- ⏰ **Задержка заказа** — предупреждение персонала
- 💰 **Оплата получена** — подтверждение расчета

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
python -m pytest tests/ -v

# Покрытие кода
pytest --cov=app tests/

# Конкретный тест
pytest tests/test_api.py::test_user_creation -v
```

### Комплексное тестирование API
```bash
# Запуск полного тестирования всех эндпоинтов
python tests/test_api.py
```

## 🚀 Развертывание

### На Raspberry Pi

1. **Подготовка системы**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git nginx -y
```

2. **Установка приложения**
```bash
git clone <repository-url>
cd qresos4/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Настройка systemd сервиса**
```bash
sudo nano /etc/systemd/system/qresos4.service
```

```ini
[Unit]
Description=QRes OS 4 Restaurant Management System
After=network.target

[Service]
Type=exec
User=pi
WorkingDirectory=/home/pi/qresos4/backend
Environment=PATH=/home/pi/qresos4/backend/venv/bin
ExecStart=/home/pi/qresos4/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Запуск сервиса**
```bash
sudo systemctl daemon-reload
sudo systemctl enable qresos4
sudo systemctl start qresos4
```

### В облаке (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### С PostgreSQL

```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: qresos4
      POSTGRES_USER: qresos4
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://qresos4:secure_password@db/qresos4
    depends_on:
      - db

volumes:
  postgres_data:
```

## 📊 Мониторинг и метрики

### Health Check
```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "uptime": 123.45
}
```

### Логирование
```python
# Настройка логирования в production
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('qresos4.log'),
        logging.StreamHandler()
    ]
)
```

## 🔧 Разработка

### Настройка окружения разработки
```bash
# Форматирование кода
black app/
isort app/

# Линтинг
flake8 app/
mypy app/

# Pre-commit hooks
pre-commit install
```

### Создание миграций
```bash
# Создание новой миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

### Добавление новой модели
1. Создать модель в `app/models/`
2. Добавить схемы в `app/schemas/`
3. Создать роутер в `app/routers/`
4. Добавить в `app/main.py`
5. Создать миграцию

## 🎯 Roadmap

### ✅ Реализовано
- [x] Система пользователей и ролей
- [x] Управление столиками и локациями
- [x] Гибкая система блюд с вариациями
- [x] Полнофункциональная система заказов
- [x] WebSocket real-time уведомления
- [x] Comprehensive API с документацией
- [x] Система аутентификации и авторизации

### 🔄 В разработке
- [ ] **Аналитика и отчеты** — детальная статистика продаж
- [ ] **Система лояльности** — бонусы и скидки для клиентов
- [ ] **Интеграция с кассой** — фискальные чеки
- [ ] **Мобильное приложение** — для персонала и клиентов

### 🚀 Планируется
- [ ] **Система складского учета** — управление остатками
- [ ] **Интеграция с платежными системами** — онлайн оплата
- [ ] **Система доставки** — интеграция с курьерскими службами
- [ ] **AI рекомендации** — умные предложения блюд
- [ ] **Система отзывов** — обратная связь от клиентов

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие QRes OS 4! Вот как вы можете помочь:

### Процесс контрибуции
1. 🍴 **Fork** репозитория
2. 🌿 **Создайте** ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. ✨ **Внесите** изменения и добавьте тесты
4. 📝 **Зафиксируйте** изменения (`git commit -m 'Add amazing feature'`)
5. 🚀 **Отправьте** изменения (`git push origin feature/amazing-feature`)
6. 🔄 **Создайте** Pull Request

### Что можно улучшить
- 🐛 **Исправление багов**
- ✨ **Новые функции**
- 📚 **Улучшение документации**
- 🧪 **Добавление тестов**
- 🌍 **Переводы интерфейса**
- 🎨 **Улучшение UI/UX**

## 🆘 Поддержка

### Получение помощи
- 📖 **Документация**: изучите файлы в папке `docs/`
- 🔍 **API справка**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🐛 **Issues**: создайте issue в GitHub
- 💬 **Discussions**: обсуждения в GitHub

### Диагностика проблем
```bash
# Проверка логов
tail -f qresos4.log

# Проверка состояния
curl http://localhost:8000/health

# Проверка базы данных
sqlite3 app.db ".tables"
```

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT License**. Подробности см. в файле [LICENSE](LICENSE).

## 👥 Команда

QRes OS 4 разрабатывается командой энтузиастов, стремящихся создать лучшую систему управления рестораном.

---

<div align="center">

**🍽️ QRes OS 4 - Будущее управления ресторанами уже здесь!**

[![GitHub stars](https://img.shields.io/github/stars/username/qresos4.svg?style=social&label=Star)](https://github.com/username/qresos4)
[![GitHub forks](https://img.shields.io/github/forks/username/qresos4.svg?style=social&label=Fork)](https://github.com/username/qresos4)

</div>
