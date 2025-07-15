# Система управления кухонными цехами и позициями заказов

## 🏭 Обзор системы

Новая система позволяет:
- Управлять позициями заказов по кухонным цехам
- Добавлять блюда к существующим заказам
- Отслеживать статусы приготовления каждого блюда
- Оптимизировать работу кухни

## 📋 Кухонные цехи (KitchenDepartment)

### Доступные цехи:
- **`BAR`** - Бар (напитки)
- **`COLD_KITCHEN`** - Холодный цех (салаты, закуски)
- **`HOT_KITCHEN`** - Горячий цех (основные блюда)
- **`DESSERT`** - Кондитерский цех
- **`GRILL`** - Гриль
- **`BAKERY`** - Выпечка

## 🔄 Статусы позиций заказа (OrderItemStatus)

### Жизненный цикл позиции:
1. **`NEW`** - Новая позиция (создана)
2. **`SENT_TO_KITCHEN`** - Отправлена на кухню
3. **`IN_PREPARATION`** - Готовится
4. **`READY`** - Готова к подаче
5. **`SERVED`** - Подана клиенту
6. **`CANCELLED`** - Отменена

## 🕐 Временные метки

Каждая позиция заказа отслеживает:
- **`sent_to_kitchen_at`** - Время отправки на кухню
- **`preparation_started_at`** - Время начала приготовления
- **`ready_at`** - Время готовности
- **`served_at`** - Время подачи
- **`estimated_preparation_time`** - Ожидаемое время приготовления (мин)
- **`actual_preparation_time`** - Фактическое время приготовления (мин)

## 🔄 Автоматическое обновление статуса заказа

Статус заказа обновляется автоматически на основе статусов позиций:

```python
# Все позиции поданы → ORDER: SERVED
if all(item.status == "served" for item in order.items):
    order.status = OrderStatus.SERVED

# Есть готовые позиции → ORDER: READY  
elif any(item.status == "ready" for item in order.items):
    order.status = OrderStatus.READY

# Есть позиции в работе → ORDER: PENDING
elif any(item.status in ["in_preparation", "sent_to_kitchen"] for item in order.items):
    order.status = OrderStatus.PENDING
```

## 📡 API эндпоинты

### Kitchen API (`/kitchen/`)

#### Получить заказы для цеха:
```http
GET /kitchen/orders?department=hot&status_filter=in_preparation,ready
```

#### Обновить статус позиции:
```http
PATCH /kitchen/items/{item_id}/status
{
  "status": "in_preparation"
}
```

#### Получить статистику цеха:
```http
GET /kitchen/departments/hot/stats?hours=24
```

### Orders API (расширенное)

#### Добавить позиции к заказу:
```http
POST /kitchen/orders/{order_id}/items
[
  {
    "dish_id": 1,
    "quantity": 2,
    "comment": "Без лука"
  }
]
```

#### Отправить позиции на кухню:
```http
POST /kitchen/orders/{order_id}/send-to-kitchen
[1, 2, 3]  // item_ids
```

## 🎯 Рабочие процессы

### Создание заказа:
1. Официант создает заказ → все позиции получают статус `IN_PREPARATION`
2. Позиции автоматически распределяются по цехам на основе `dish.department`
3. Заказ переходит в статус `PENDING`

### Работа кухни:
1. Кухня получает позиции сразу со статусом `IN_PREPARATION`
2. По готовности → `READY`
3. Официант подает → `SERVED`

### Дополнение заказа:
1. Гости в статусе `DINING` могут дозаказать
2. Новые позиции добавляются со статусом `IN_PREPARATION`
3. Заказ остается в статусе `DINING`
4. Новые позиции проходят стандартный цикл

## 📊 Преимущества новой системы

### Для кухни:
- **Разделение по цехам** - каждый цех видит только свои задачи
- **Приоритизация** - заказы сортируются по времени создания
- **Отслеживание времени** - контроль времени приготовления
- **Статистика** - анализ производительности цехов

### Для официантов:
- **Частичная подача** - можно подавать готовые блюда
- **Дозаказ** - добавление блюд к активным заказам
- **Контроль** - отслеживание статуса каждого блюда

### Для менеджмента:
- **Аналитика** - детальная статистика по цехам
- **Оптимизация** - выявление узких мест
- **Планирование** - прогнозирование нагрузки

## 🛠️ Техническая реализация

### Модели данных:
```python
class OrderItem(Base):
    # Основные поля
    status: OrderItemStatus = OrderItemStatus.IN_PREPARATION
    department: KitchenDepartment  # Цех
    
    # Временные метки
    sent_to_kitchen_at: Optional[datetime]
    preparation_started_at: Optional[datetime]
    ready_at: Optional[datetime]
    served_at: Optional[datetime]
    
    # Время приготовления
    estimated_preparation_time: Optional[int]
    actual_preparation_time: Optional[int]
```

### Сервисы:
- **`KitchenService`** - управление кухонными операциями
- **`OrderService`** - обновлен для работы с новой системой

### Безопасность:
- **Роли доступа** - кухня, официанты, админы
- **Валидация** - проверка прав на операции
- **Логирование** - отслеживание всех изменений

Система готова к использованию! 🚀
