# 🍽️ QRes OS 4 - Restaurant Management System

Современная система управления рестораном, построенная на FastAPI и SQLAlchemy с поддержкой асинхронных операций.

## 🚀 Особенности

- **Modern Stack**: FastAPI + SQLAlchemy 2.0 + Async/Await
- **Dish Variations**: Гибкая система вариаций блюд с индивидуальными ценами
- **Multi-Role Support**: Администраторы, официанты, кухня
- **Real-time Communication**: WebSocket для живого взаимодействия
- **QR Menu System**: QR-коды для каждого столика
- **PIN Authentication**: Быстрый вход по PIN-коду
- **Comprehensive API**: REST API с автоматической документацией
- **Production Ready**: Готово для развертывания на Raspberry Pi

## 📋 Требования

- Python 3.9+
- SQLite (по умолчанию) или PostgreSQL/MySQL
- 512MB RAM (минимум для Raspberry Pi)

## 🔧 Установка и запуск

### 1. Клонирование и установка зависимостей

```bash
git clone <repository-url>
cd qresos4/backend
pip install -r requirements.txt
```

### 2. Настройка окружения

Создайте файл `.env` и настройте переменные:

```bash
# Скопируйте .env.example в .env и отредактируйте
cp .env.example .env
```

### 3. Инициализация базы данных

```bash
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('База данных инициализирована!')
"
```

### 4. Запуск сервера

```bash
uvicorn app.main:app --reload
```

Или для продакшена:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🏗️ Архитектура

```
app/
├── main.py              # Точка входа FastAPI
├── config.py            # Конфигурация приложения
├── database.py          # Настройка базы данных
├── deps.py              # Зависимости FastAPI
├── models/              # SQLAlchemy модели
│   ├── __init__.py
│   ├── user.py
│   ├── table.py
│   ├── location.py
│   ├── category.py
│   ├── dish.py
│   ├── dish_variation.py  # 🆕 Вариации блюд
│   ├── order.py
│   ├── order_item.py
│   ├── ingredient.py
│   └── paymentmethod.py
├── schemas/             # Pydantic схемы
│   ├── __init__.py
│   ├── user.py
│   ├── table.py
│   ├── location.py
│   ├── category.py
│   ├── dish.py
│   ├── dish_variation.py  # 🆕 Схемы вариаций
│   ├── order.py
│   ├── order_item.py
│   ├── ingredient.py
│   └── paymentmethod.py
├── routers/             # FastAPI роутеры
│   ├── __init__.py
│   ├── auth.py
│   ├── users.py
│   ├── tables.py
│   ├── locations.py
│   ├── categories.py
│   ├── dishes.py        # 🆕 Включает вариации
│   ├── orders.py
│   ├── order_items.py
│   ├── ingredients.py
│   ├── paymentmethod.py
│   └── websocket.py
└── services/            # Бизнес-логика
    ├── __init__.py
    ├── auth.py
    └── utils.py
```

## 🔐 Аутентификация

Система поддерживает два способа аутентификации:

1. **Стандартная**: логин + пароль
2. **PIN-код**: быстрый вход для сотрудников

Все API эндпоинты защищены JWT токенами с проверкой ролей.

## 📱 API Эндпоинты

### Аутентификация
- `POST /auth/login` - Вход по логину/паролю
- `POST /auth/login-pin` - Вход по PIN-коду
- `GET /auth/me` - Информация о текущем пользователе

### Пользователи (только для администраторов)
- `GET /users/` - Список пользователей
- `POST /users/` - Создание пользователя
- `GET /users/{id}` - Информация о пользователе
- `PATCH /users/{id}` - Обновление пользователя

### Столики
- `GET /tables/` - Список столиков
- `POST /tables/` - Создание столика (админ)
- `PATCH /tables/{id}/status` - Изменение статуса (официант)
- `GET /tables/{id}/qr` - QR-код столика

### Локации
- `GET /locations/` - Список зон ресторана
- `POST /locations/` - Создание зоны (админ)
- `GET /locations/{id}/tables` - Столики в зоне

### Категории и блюда
- `GET /categories/` - Список категорий
- `GET /dishes/` - Список блюд
- `GET /dishes/menu` - Публичное меню для клиентов
- `PATCH /dishes/{id}/availability` - Изменение доступности

### 🆕 Вариации блюд
- `GET /dishes/{dish_id}/variations/` - Список вариаций блюда
- `POST /dishes/{dish_id}/variations/` - Создание вариации
- `GET /dishes/{dish_id}/variations/{variation_id}` - Получение вариации
- `PATCH /dishes/{dish_id}/variations/{variation_id}` - Обновление вариации
- `DELETE /dishes/{dish_id}/variations/{variation_id}` - Удаление вариации

### Заказы
- `GET /orders/` - Список заказов
- `POST /orders/` - Создание заказа
- `GET /orders/{id}` - Информация о заказе
- `PATCH /orders/{id}` - Обновление заказа
- `POST /orders/{order_id}/items/` - Добавление блюда в заказ
- `PATCH /orders/{order_id}/items/{item_id}` - Обновление позиции

### Ингредиенты
- `GET /ingredients/` - Список ингредиентов
- `POST /ingredients/` - Создание ингредиента (админ)
- `PATCH /ingredients/{id}` - Обновление ингредиента

### Способы оплаты
- `GET /payment-methods/` - Список способов оплаты
- `POST /payment-methods/` - Создание способа оплаты (админ)
- `PATCH /payment-methods/{id}` - Обновление способа оплаты

### WebSocket
- `WS /ws/orders` - Real-time связь официант ↔ кухня

## 📖 API Документация

После запуска сервера документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🆕 Новая архитектура блюд

Система теперь поддерживает гибкие вариации блюд:

### Dish (Блюдо)
- Общая информация о блюде без цены
- Основное изображение и описание
- Связь с категорией

### DishVariation (Вариация блюда)
- Конкретная вариация с ценой
- Индивидуальное название (например: "Маленькая", "Большая")
- Собственное изображение и описание
- Вес, калорийность, доступность

### Преимущества:
- Одно блюдо может иметь разные размеры/варианты
- Гибкое ценообразование
- Простое управление наличием конкретных вариаций
- Удобство для клиентов при выборе

## 🧪 Тестирование

Запуск тестов:

```bash
python -m pytest tests/ -v
```

Или используйте встроенный скрипт:

```bash
python run_tests.py
```

## 🔧 Конфигурация

Основные переменные окружения в `.env`:

```env
# База данных
DATABASE_URL=sqlite+aiosqlite:///./app.db

# Безопасность
SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Сервер
HOST=0.0.0.0
PORT=8000

# CORS для фронтенда
CORS_ORIGINS=["http://localhost:3000", "http://192.168.1.*"]

# QR-коды
QR_BASE_URL=http://192.168.1.100:8000/menu
```

## 🌐 Развертывание на Raspberry Pi

### Системные требования
- Raspberry Pi 4 (2GB RAM рекомендуется)
- Ubuntu Server 24.04 LTS
- Python 3.9+

### Быстрая установка

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3 python3-pip python3-venv git -y

# Клонирование проекта
git clone <repository-url>
cd qresos4/backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Инициализация БД
python -c "
from app.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print('База данных инициализирована!')
"

# Запуск в фоне
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

## 📊 Мониторинг

Проверка состояния системы:

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "uptime": 123.45
}
```

## 📁 Структура файлов

- `app.db` - База данных SQLite
- `uploads/` - Загруженные изображения
- `alembic/` - Миграции базы данных
- `tests/` - Тесты приложения
- `docs/` - Подробная документация

## 🔍 Разработка

### Форматирование кода

```bash
black app/
isort app/
```

### Добавление миграций

```bash
alembic revision --autogenerate -m "Описание изменений"
alembic upgrade head
```

## 🎯 Roadmap

- [x] Система заказов и позиций ✅
- [x] Вариации блюд с индивидуальными ценами ✅
- [x] WebSocket уведомления ✅
- [x] Роутеры для ингредиентов и способов оплаты ✅
- [ ] Отчеты и аналитика
- [ ] Система складского учета
- [ ] Интеграция с платежными системами
- [ ] Мобильное приложение
- [ ] Интеграция с принтерами чеков

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Отправьте Pull Request

## 📝 Лицензия

MIT License

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию API](http://localhost:8000/docs)
2. Изучите файлы в папке `docs/`
3. Обратитесь к логам: `tail -f nohup.out`
