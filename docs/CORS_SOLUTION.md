# Решение проблемы CORS в QRes OS 4

## Проблема
FastAPI приложение не работало с конкретными CORS origins при указании в настройках `settings.cors_origins`, но работало с wildcard `allow_origins=["*"]`. При попытке указать конкретные домены фронтенда, сервер отвечал "Disallowed CORS origin" на preflight запросы.

**ОБНОВЛЕНИЕ 13.07.2025**: Обнаружена дополнительная проблема с PATCH запросами - метод PATCH не был включен в список разрешенных методов `allow_methods`, что вызывало ошибку 400 на preflight запросах для эндпоинтов обновления статусов.

## Причины проблемы
1. **Неправильный формат в .env файле** - использовался JSON формат `["origin1", "origin2"]` вместо строки с запятыми
2. **Конфликт парсинга Pydantic** - автоматический парсинг List[str] пытался интерпретировать строку как JSON
3. **Отсутствие нужных URL-адресов** - не было указано `http://localhost:5173` для Vite dev server
4. **ОТСУТСТВИЕ PATCH МЕТОДА** - метод PATCH не был включен в `allow_methods`, что блокировало все PATCH запросы на изменение статусов

## Решение

### 1. Конфигурация в config.py
```python
# CORS - Конфигурируем origins в зависимости от окружения
cors_origins: List[str] = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173", 
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080"
]

@validator('cors_origins', pre=True, allow_reuse=True)
def parse_cors_origins(cls, v) -> List[str]:
    """Парсинг CORS origins из переменной окружения или списка"""
    if isinstance(v, str):
        # Удаляем возможные JSON скобки и кавычки
        v = v.strip().strip('[]"\'')
        if not v:  # Если строка пустая, возвращаем значения по умолчанию
            return [
                "http://localhost:5173", 
                "http://127.0.0.1:5173", 
                "http://localhost:3000", 
                "http://127.0.0.1:3000",
                "http://localhost:8080",
                "http://127.0.0.1:8080"
            ]
        origins = [origin.strip().strip('"\'') for origin in v.split(",")]
        # Фильтруем пустые строки
        origins = [origin for origin in origins if origin]
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"🔧 CORS Origins загружены из строки: {origins}")
        return origins
    elif isinstance(v, list):
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"🔧 CORS Origins загружены как список: {v}")
        return v
    else:
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"⚠️ Неожиданный тип CORS Origins: {type(v)}, значение: {v}")
        return [str(v)] if v else []
```

### 2. Конфигурация в .env файле
```env
# CORS - Frontend URLs (Vite dev server + autres) 
# Раскомментируйте и настройте при необходимости
# CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080
```

**Правильный формат:** строка с разделителями-запятыми
**Неправильный формат:** `["http://localhost:5173", "http://localhost:3000"]`

### 3. Настройка CORS middleware в main.py
```python
# CORS Middleware - настроен для разработки фронтенда
if settings.debug:
    print(f"🚀 Настройка CORS для origins: {settings.cors_origins}")
    print(f"🔧 Debug режим: {settings.debug}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Используем настройки из конфига
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # ✅ PATCH добавлен!
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    expose_headers=[
        "Content-Length",
        "X-Total-Count",
        "X-Page-Count"
    ]
)
```

### 4. Отладочный эндпоинт
Добавлен эндпоинт `/debug/cors` для проверки конфигурации:
```python
@app.get("/debug/cors", tags=["Debug"])
async def debug_cors(request: Request):
    """Отладочный эндпоинт для проверки CORS настроек"""
    origin = request.headers.get("origin", "Не указан")
    
    return {
        "message": "CORS Debug Information",
        "configured_origins": settings.cors_origins,
        "request_origin": origin,
        "origin_allowed": origin in settings.cors_origins,
        "cors_config": {
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
            "expose_headers": ["*"]
        },
        "environment": settings.environment,
        "debug": settings.debug
    }
```

## Тестирование решения

### Успешные тесты
```bash
# Preflight запрос с разрешенным origin
curl -X OPTIONS "http://localhost:8000/health" \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Ответ: HTTP 200 OK с заголовками CORS
< access-control-allow-origin: http://localhost:5173
< access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS
< access-control-allow-credentials: true

# Обычный GET запрос
curl -X GET "http://localhost:8000/health" \
  -H "Origin: http://localhost:5173" \
  -v

# Ответ: HTTP 200 OK с заголовками CORS
< access-control-allow-origin: http://localhost:5173
< access-control-allow-credentials: true
```

### Отклоненные запросы
```bash
# Preflight запрос с неразрешенным origin
curl -X OPTIONS "http://localhost:8000/health" \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Ответ: HTTP 400 Bad Request
< HTTP/1.1 400 Bad Request
Disallowed CORS origin
```

## Результат
✅ **CORS теперь работает корректно:**
- Разрешенные origins получают правильные заголовки CORS
- Неразрешенные origins отклоняются с ошибкой 400
- Поддерживается настройка через переменные окружения
- Есть fallback значения по умолчанию
- Добавлена отладочная информация в dev режиме

## Настройка для продакшена
В продакшене рекомендуется:
1. Указать конкретные домены в `CORS_ORIGINS`
2. Установить `DEBUG=False`
3. Удалить или заблокировать доступ к `/debug/cors`
4. Использовать HTTPS origins: `https://yourdomain.com`

## Поддерживаемые origins для разработки
- `http://localhost:5173` - Vite dev server
- `http://127.0.0.1:5173` - Vite dev server (альтернативный хост)
- `http://localhost:3000` - React/Next.js dev server
- `http://127.0.0.1:3000` - React/Next.js dev server (альтернативный хост)
- `http://localhost:8080` - Vue CLI dev server
- `http://127.0.0.1:8080` - Vue CLI dev server (альтернативный хост)
