# API Эндпоинты и структуры моделей

## Категории
- GET /categories
- POST /categories
- PUT /categories/{id}
- DELETE /categories/{id}
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
- POST /dishes
- PUT /dishes/{id}
- DELETE /dishes/{id}
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
- PUT /dish-variations/{id}
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
    - created_at: datetime
    - updated_at: datetime

## Ингредиенты
- GET /ingredients
- POST /ingredients
- PUT /ingredients/{id}
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
- POST /locations
- PUT /locations/{id}
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
- PUT /tables/{id}
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
    - created_at: datetime
    - updated_at: datetime

## Заказы
- GET /orders
- POST /orders
- PUT /orders/{id}
- DELETE /orders/{id}
- **Поля:**
    - id: int
    - total_price: float
    - status: enum (pending, ready, served, dining, completed, cancelled)
    - payment_status: enum (unpaid, paid, refunded)
    - order_type: enum (dine_in, takeaway, delivery)
    - table_id: int
    - user_id: int
    - created_at: datetime
    - updated_at: datetime
    - payment_method_id: int | null
    - delivery_address: str | null
    - delivery_phone: str | null
    - items: list[OrderItem]

## Элементы заказа
- GET /order-items
- POST /order-items
- PUT /order-items/{id}
- DELETE /order-items/{id}
- **Поля:**
    - id: int
    - order_id: int
    - dish_id: int
    - variation_id: int | null
    - quantity: int
    - status: enum (new, sent_to_kitchen, in_preparation, ready, served, cancelled)
    - kitchen_department_id: enum (bar, cold, hot, dessert, grill, bakery)
    - created_at: datetime
    - updated_at: datetime

## Методы оплаты
- GET /payment-methods
- POST /payment-methods
- PUT /payment-methods/{id}
- DELETE /payment-methods/{id}
- **Поля:**
    - id: int
    - name: str
    - is_active: bool
    - created_at: datetime
    - updated_at: datetime

## Пользователи
- GET /users
- POST /users
- PUT /users/{id}
- DELETE /users/{id}
- **Поля:**
    - id: int
    - username: str
    - password_hash: str
    - full_name: str
    - role: enum (admin, waiter, kitchen)
    - is_active: bool
    - shift_active: bool
    - created_at: datetime
    - updated_at: datetime

## Аутентификация
- POST /auth/login
- POST /auth/logout
- GET /auth/me

## Kitchen
- GET /kitchen/orders
- PUT /kitchen/order-items/{id}/status

## WebSocket
- /ws

---
*Для подробностей см. схемы моделей и документацию.*
