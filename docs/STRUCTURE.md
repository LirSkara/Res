# 📁 Структура проекта QRes OS 4

```
qresos4/backend/
├── .env                    # Конфигурация окружения
├── .env.example           # Пример конфигурации
├── .gitignore             # Игнорируемые git файлы
├── README.md              # 📖 Основная документация
├── requirements.txt       # Python зависимости
├── run_tests.py          # Скрипт запуска тестов
├── alembic.ini           # Конфигурация миграций
├── app.db                # 🗄️ База данных SQLite
│
├── alembic/              # 🔄 Миграции базы данных
│   ├── env.py
│   ├── script.py.mako
│   └── versions/         # Файлы миграций
│
├── app/                  # 🚀 Основное приложение
│   ├── main.py           # Точка входа FastAPI
│   ├── config.py         # Настройки приложения
│   ├── database.py       # Подключение к БД
│   ├── deps.py           # Зависимости FastAPI
│   │
│   ├── models/           # 🗃️ SQLAlchemy модели
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── table.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── dish.py
│   │   ├── dish_variation.py    # 🆕 Вариации блюд
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── ingredient.py
│   │   └── paymentmethod.py
│   │
│   ├── schemas/          # 📋 Pydantic схемы
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── table.py
│   │   ├── location.py
│   │   ├── category.py
│   │   ├── dish.py
│   │   ├── dish_variation.py    # 🆕 Схемы вариаций
│   │   ├── order.py
│   │   ├── order_item.py
│   │   ├── ingredient.py
│   │   └── paymentmethod.py
│   │
│   ├── routers/          # 🌐 FastAPI роутеры
│   │   ├── __init__.py
│   │   ├── auth.py           # Аутентификация
│   │   ├── users.py          # Управление пользователями
│   │   ├── tables.py         # Столики
│   │   ├── locations.py      # Зоны ресторана
│   │   ├── categories.py     # Категории блюд
│   │   ├── dishes.py         # Блюда + вариации
│   │   ├── orders.py         # Заказы
│   │   ├── order_items.py    # Позиции заказов
│   │   ├── ingredients.py    # Ингредиенты
│   │   ├── paymentmethod.py  # Способы оплаты
│   │   └── websocket.py      # WebSocket связь
│   │
│   └── services/         # ⚙️ Бизнес-логика
│       ├── __init__.py
│       ├── auth.py       # Сервисы аутентификации
│       └── utils.py      # Утилиты
│
├── docs/                 # 📚 Документация
│   ├── README.md         # Подробная документация
│   ├── target.txt        # Техническое задание
│   └── DEPLOYMENT_GUIDE.md  # Руководство по развертыванию
│
├── tests/                # 🧪 Тесты
│   └── test_api.py       # API тесты
│
├── uploads/              # 📷 Загруженные файлы
│   └── (изображения блюд, аватары)
│
└── venv/                 # 🐍 Виртуальное окружение Python
    └── (библиотеки)
```

## 🔑 Ключевые особенности структуры

### 🆕 Новая архитектура блюд
- `models/dish.py` - блюдо без цены
- `models/dish_variation.py` - вариации с ценами
- `routers/dishes.py` - объединенные endpoints

### 🗄️ База данных
- Единый файл `app.db` (SQLite)
- Миграции через Alembic
- Async/await поддержка

### 🌐 API структура
- Роль-ориентированные роутеры
- JWT аутентификация  
- WebSocket для real-time

### 📁 Организация кода
- Четкое разделение моделей и схем
- Централизованная конфигурация
- Модульная структура сервисов

## 🚀 Быстрый старт

1. **Установка**: `pip install -r requirements.txt`
2. **Конфигурация**: `cp .env.example .env`
3. **Инициализация БД**: См. README.md
4. **Запуск**: `uvicorn app.main:app --reload`

## 📖 Документация

- **API**: http://localhost:8000/docs
- **Основная**: [README.md](README.md)
- **Техническая**: [docs/](docs/)
