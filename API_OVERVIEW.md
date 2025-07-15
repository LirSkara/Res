# API Эндпоинты и структуры моделей

## Категории
- GET /categories
- POST /categories
- PATCH /categories/{id}
- DELETE /categories/{id}
- GET /categories/{id}
- GET /categories/{id}/dishes
- **Поля:**
    - id: int
    - name: str
    - description: str | null
    - image_url: str | null
    - sort_order: int
    - is_active: bool
    - color: str | null
    - featured: bool
    - created_at: datetime
    - updated_at: datetime

## Блюда
- GET /dishes
- GET /dishes/menu
- POST /dishes
- GET /dishes/{id}
- PATCH /dishes/{id}
- PATCH /dishes/{id}/availability
- DELETE /dishes/{id}
- GET /dishes/{id}/variations/
- POST /dishes/{id}/variations/
- GET /dishes/{id}/variations/{variation_id}
- PATCH /dishes/{id}/variations/{variation_id}
- PATCH /dishes/{id}/variations/{variation_id}/availability
- DELETE /dishes/{id}/variations/{variation_id}
- **Поля:**
    - id: int
    - name: str
    - description: str
    - code: str | null
    - main_image_url: str | null
    - is_available: bool
    - sort_order: int
    - is_popular: bool
    - category_id: int
    - cooking_time: int | null
    - weight: float | null
    - calories: int | null
    - ingredients: str | null
    - department: enum (bar, cold, hot, dessert, grill, bakery)
    - created_at: datetime
    - updated_at: datetime

## Вариации блюда
- GET /dish-variations
- POST /dish-variations
- GET /dish-variations/{id}
- PATCH /dish-variations/{id}
- DELETE /dish-variations/{id}
- **Поля:**
    - id: int
    - name: str
    - description: str | null
    - price: float
    - image_url: str | null
    - weight: float | null
    - calories: int | null
    - is_default: bool
    - is_available: bool
    - sort_order: int
    - dish_id: int
    - sku: str | null
    - created_at: datetime
    - updated_at: datetime

## Ингредиенты
- GET /ingredients
- GET /ingredients/allergens/list
- POST /ingredients
- GET /ingredients/{id}
- PATCH /ingredients/{id}
- DELETE /ingredients/{id}
- **Поля:**
    - id: int
    - name: str
    - description: str | null
    - is_allergen: bool
    - created_at: datetime
    - updated_at: datetime

## Локации
- GET /locations
- GET /locations/admin/integrity-check
- POST /locations/admin/auto-fix
- POST /locations
- GET /locations/{id}
- PATCH /locations/{id}
- PATCH /locations/{id}/sync-tables
- GET /locations/{id}/tables
- DELETE /locations/{id}
- **Поля:**
    - id: int
    - name: str
    - description: str | null
    - color: str | null
    - is_active: bool
    - created_at: datetime
    - updated_at: datetime

## Столы
- GET /tables
- POST /tables
- GET /tables/{id}
- PATCH /tables/{id}
- PATCH /tables/{id}/status
- GET /tables/{id}/qr
- GET /tables/{id}/sync-status
- PATCH /tables/{id}/force-sync
- DELETE /tables/{id}
- **Поля:**
    - id: int
    - number: int
    - qr_code: str
    - seats: int
    - is_occupied: bool
    - is_active: bool
    - description: str | null
    - location_id: int
    - current_order_id: int | null
    - created_at: datetime
    - updated_at: datetime

## Заказы
- GET /orders
- GET /orders/stats/summary
- POST /orders
- POST /orders/delivery
- GET /orders/{id}
- PATCH /orders/{id}/status
- PATCH /orders/{id}/payment
- POST /orders/{id}/complete-payment
- DELETE /orders/{id}
- **Поля:**
    - id: int
    - total_price: float
    - status: enum (pending, ready, served, dining, completed, cancelled)
    - payment_status: enum (unpaid, paid, refunded)
    - order_type: enum (dine_in, takeaway, delivery)
    - table_id: int | null
    - waiter_id: int
    - payment_method_id: int | null
    - customer_name: str | null
    - customer_phone: str | null
    - delivery_address: str | null
    - delivery_notes: str | null
    - served_at: datetime | null
    - cancelled_at: datetime | null
    - completed_at: datetime | null
    - time_to_serve: int | null
    - created_at: datetime
    - updated_at: datetime
    - items: list[OrderItem]

## Элементы заказа
- GET /order-items
- POST /order-items
- GET /order-items/{id}
- PATCH /order-items/{id}
- DELETE /order-items/{id}
- POST /orders/{order_id}/items/
- PATCH /orders/{order_id}/items/{item_id}
- PATCH /orders/{order_id}/items/{item_id}/status
- DELETE /orders/{order_id}/items/{item_id}
- **Поля:**
    - id: int
    - order_id: int
    - dish_id: int
    - dish_variation_id: int | null
    - quantity: int
    - price: float
    - total: float
    - status: enum (new, sent_to_kitchen, in_preparation, ready, served, cancelled)
    - department: enum (bar, cold, hot, dessert, grill, bakery)
    - sent_to_kitchen_at: datetime | null
    - preparation_started_at: datetime | null
    - ready_at: datetime | null
    - served_at: datetime | null
    - estimated_preparation_time: int | null
    - actual_preparation_time: int | null
    - created_at: datetime
    - updated_at: datetime

## Методы оплаты
- GET /payment-methods
- GET /payment-methods/active
- POST /payment-methods
- GET /payment-methods/{id}
- PATCH /payment-methods/{id}
- DELETE /payment-methods/{id}
- **Поля:**
    - id: int
    - name: str
    - is_active: bool
    - created_at: datetime
    - updated_at: datetime

## Пользователи
- GET /users
- GET /users/waiters
- GET /users/kitchen
- POST /users
- GET /users/{id}
- PATCH /users/{id}
- PATCH /users/{id}/password
- DELETE /users/{id}
- **Поля:**
    - id: int
    - username: str
    - password_hash: str
    - full_name: str
    - role: enum (admin, waiter, kitchen)
    - is_active: bool
    - shift_active: bool
    - phone: str | null
    - passport: str | null
    - avatar_url: str | null
    - pin_code: str | null
    - created_by_id: int | null
    - last_login: datetime | null
    - created_at: datetime
    - updated_at: datetime

## Аутентификация
- POST /auth/login
- POST /auth/login/pin
- GET /auth/me
- POST /auth/logout

## Дашборд
- GET /dashboard/stats

## Kitchen
- GET /kitchen/orders
- GET /kitchen/departments
- GET /kitchen/departments/{department}/stats
- PATCH /kitchen/items/{id}/status
- POST /kitchen/orders/{order_id}/items
- POST /kitchen/orders/{order_id}/send-to-kitchen

## WebSocket
- /ws - Real-time коммуникация между официантами и кухней

## Дополнительные эндпоинты

### Статистика и аналитика:
- GET /dashboard/stats - Общая статистика системы
- GET /orders/stats/summary - Статистика заказов
- GET /kitchen/departments/{department}/stats - Статистика кухонного цеха

### Специальные операции:
- GET /locations/admin/integrity-check - Проверка целостности данных локаций
- POST /locations/admin/auto-fix - Автоматическое исправление проблем
- PATCH /locations/{id}/sync-tables - Синхронизация столов локации
- GET /tables/{id}/qr - Получение QR-кода стола
- GET /tables/{id}/sync-status - Статус синхронизации стола
- PATCH /tables/{id}/force-sync - Принудительная синхронизация стола

### Управление доступностью:
- PATCH /dishes/{id}/availability - Изменение доступности блюда
- PATCH /dishes/{id}/variations/{variation_id}/availability - Изменение доступности вариации

### Специфичные для ролей:
- GET /users/waiters - Список официантов
- GET /users/kitchen - Список кухонных работников
- GET /ingredients/allergens/list - Список аллергенов
- GET /payment-methods/active - Активные способы оплаты

---
*Для подробностей см. схемы моделей и документацию. Все эндпоинты используют PATCH для обновления данных вместо PUT.*
