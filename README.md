# 🍽️ QRes OS 4 - Restaurant Management System

Современная система управления рестораном, построенная на FastAPI и SQLAlchemy с поддержкой асинхронных операций.

## 🚀 Особенности

- **Modern Stack**: FastAPI + SQLAlchemy 2.0 + Async/Await
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

Скопируйте `.env.example` в `.env` и настройте переменные:

```bash
cp .env .env.local
# Отредактируйте .env.local под ваши нужды
```

### 3. Инициализация базы данных

```bash
python init_db.py
```

Эта команда создаст:
- Таблицы базы данных
- Администратора по умолчанию
- Демо-пользователей
- Базовые локации и категории

### 4. Запуск сервера

```bash
uvicorn app.main:app --reload
```

Или для продакшена:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 👥 Пользователи по умолчанию

После инициализации будут созданы следующие пользователи:

| Роль | Логин | Пароль | PIN |
|------|-------|---------|-----|
| Администратор | `admin` | `admin123` | `1234` |
| Официант | `waiter1` | `waiter123` | `1111` |
| Кухня | `chef1` | `chef123` | `2222` |

## 📖 API Документация

После запуска сервера документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗️ Архитектура

```
app/
├── main.py              # Точка входа FastAPI
├── config.py            # Конфигурация приложения
├── database.py          # Настройка базы данных
├── deps.py              # Зависимости FastAPI
├── models/              # SQLAlchemy модели
│   ├── user.py
│   ├── table.py
│   ├── location.py
│   ├── category.py
│   ├── dish.py
│   └── order.py
├── schemas/             # Pydantic схемы
│   ├── user.py
│   ├── table.py
│   └── ...
├── routers/             # FastAPI роутеры
│   ├── auth.py
│   ├── users.py
│   ├── tables.py
│   └── ...
└── services/            # Бизнес-логика
    ├── auth.py
    └── ...
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

# Инициализация
python init_db.py

# Запуск в фоне
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

## 🔧 Конфигурация

Основные переменные окружения в `.env`:

```env
# База данных
DATABASE_URL=sqlite+aiosqlite:///./qres_os4.db

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

## 🧪 Разработка

### Установка зависимостей для разработки

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort
```

### Форматирование кода

```bash
black app/
isort app/
```

### Тестирование

```bash
pytest
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

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Отправьте Pull Request

## 📝 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 🆘 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [документацию API](http://localhost:8000/docs)
2. Откройте [Issue](https://github.com/your-repo/issues)
3. Обратитесь к логам: `tail -f nohup.out`

## 🎯 Roadmap

- [x] Система заказов и позиций ✅
- [x] WebSocket уведомления ✅
- [x] Роутеры для ингредиентов и способов оплаты ✅
- [ ] Отчеты и аналитика
- [ ] Система складского учета
- [ ] Интеграция с платежными системами
- [ ] Мобильное приложение
- [ ] Интеграция с принтерами чеков
