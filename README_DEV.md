# 🍽️ QRes OS 4 - Руководство разработчика

## 🚀 Быстрый старт

### Для разработки (Mac/Linux)

```bash
# Клонирование и переход в проект
cd backend

# Запуск в режиме разработки
./start-dev.sh
```

Сервер будет доступен на http://127.0.0.1:8000

### Для продакшена (Raspberry Pi)

```bash
# Настройка автозапуска
sudo ./setup-autostart.sh

# Или ручной запуск
./start.sh
```

## 📁 Структура проекта

```
backend/
├── app/                    # Основное приложение
│   ├── models/            # Модели базы данных
│   ├── routers/           # API маршруты
│   ├── schemas/           # Pydantic схемы
│   ├── services/          # Бизнес-логика
│   └── main.py           # Точка входа FastAPI
├── alembic/              # Миграции базы данных
├── logs/                 # Логи приложения
├── tests/                # Тесты
├── start.sh              # Продакшен запуск
├── start-dev.sh          # Разработка запуск
├── setup-autostart.sh    # Настройка автозапуска
├── qresos-control.sh     # Управление сервисом
└── requirements.txt      # Python зависимости
```

## 🛠️ Команды разработки

### Управление сервером

```bash
# Разработка
./start-dev.sh                  # Запуск с hot-reload

# Продакшен
./start.sh                      # Обычный запуск
sudo qresos-control start       # Через systemd
sudo qresos-control status      # Статус сервиса
sudo qresos-control logs        # Просмотр логов
```

### Управление базой данных

```bash
# Создание миграции
python3 -m alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
python3 -m alembic upgrade head

# Откат миграции
python3 -m alembic downgrade -1

# Создание администратора
python3 create_admin.py
```

### Тестирование

```bash
# Запуск всех тестов
python3 -m pytest

# Запуск с покрытием
python3 -m pytest --cov=app

# Запуск конкретного теста
python3 -m pytest tests/test_api.py::test_function
```

## 🌐 Конфигурация сети

### Файлы конфигурации

- **`.env.dev`** - настройки для разработки (127.0.0.1)
- **`.env`** - настройки для продакшена (192.168.4.1)
- **`network.conf`** - сетевые параметры

### Переменные окружения

| Переменная | Разработка | Продакшен | Описание |
|------------|------------|-----------|----------|
| `HOST` | 127.0.0.1 | 192.168.4.1 | IP адрес сервера |
| `PORT` | 8000 | 8000 | Порт сервера |
| `DEBUG` | true | false | Режим отладки |
| `RELOAD` | true | false | Автоперезагрузка |
| `LOG_LEVEL` | debug | info | Уровень логирования |

## 🔧 Полезные команды

### Просмотр логов

```bash
# Логи приложения
tail -f logs/app.log

# Системные логи (продакшен)
sudo journalctl -u qresos-backend -f

# Логи через control script
sudo qresos-control logs
```

### Мониторинг

```bash
# Статус процессов
ps aux | grep uvicorn

# Сетевые соединения
sudo ss -tulpn | grep :8000

# Использование ресурсов
top -p $(pgrep -f uvicorn)
```

### Резервное копирование

```bash
# Создать бэкап БД
sudo qresos-control backup

# Ручной бэкап
cp app.db backup_$(date +%Y%m%d_%H%M%S).db
```

## 🐛 Отладка

### Частые проблемы

1. **Ошибка "Can't assign requested address"**
   - Используйте `./start-dev.sh` для разработки
   - Проверьте сетевую конфигурацию для продакшена

2. **Ошибки миграций**
   ```bash
   # Проверить статус миграций
   python3 -m alembic current
   
   # Применить принудительно
   python3 -m alembic stamp head
   ```

3. **Проблемы с зависимостями**
   ```bash
   # Пересоздать виртуальное окружение
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📚 API Документация

После запуска сервера документация доступна:

- **Swagger UI**: http://127.0.0.1:8000/docs (разработка)
- **ReDoc**: http://127.0.0.1:8000/redoc (разработка)
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

## 🏗️ Развертывание

### Разработка → Продакшен

1. Тестирование локально с `./start-dev.sh`
2. Коммит изменений в git
3. Деплой на Raspberry Pi
4. Настройка автозапуска с `sudo ./setup-autostart.sh`
5. Проверка работы с `sudo qresos-control status`

### Обновление продакшена

```bash
# Остановить сервис
sudo qresos-control stop

# Обновить код
git pull

# Применить миграции
sudo qresos-control migrate

# Запустить сервис
sudo qresos-control start
```
