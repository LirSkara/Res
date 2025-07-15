# Оптимизация рабочего процесса кухни

## 🎯 Цель изменений

Упростить рабочий процесс кухни, убрав лишние промежуточные статусы и сделав работу более эффективной.

## 📋 Основные изменения

### 1. Упрощенный рабочий процесс кухни
**Старый процесс:**
1. Кухня видит позиции со статусом `NEW`
2. Повар переводит позицию в `IN_PREPARATION`
3. По готовности → `READY`
4. Официант подает → `SERVED`

**Новый процесс:**
1. Кухня получает позиции сразу со статусом `IN_PREPARATION`
2. По готовности → `READY`
3. Официант подает → `SERVED`

### 2. Автоматическая установка времени начала приготовления
- При создании позиции заказа автоматически устанавливается `preparation_started_at`
- Время приготовления рассчитывается от момента создания до готовности

## 🔧 Технические изменения

### Модель OrderItem
```python
class OrderItem(Base):
    # Статус по умолчанию изменен на IN_PREPARATION
    status: Mapped[OrderItemStatus] = mapped_column(
        SQLEnum(OrderItemStatus), 
        default=OrderItemStatus.IN_PREPARATION,  # Было: NEW
        nullable=False
    )
```

### Создание позиций заказа
```python
# При создании заказа
new_item = OrderItem(
    # ...другие поля...
    status=OrderItemStatus.IN_PREPARATION,
    preparation_started_at=datetime.utcnow()  # Автоматически
)

# При добавлении блюда к заказу
new_item = OrderItem(
    # ...другие поля...
    status=OrderItemStatus.IN_PREPARATION,
    preparation_started_at=datetime.utcnow()  # Автоматически
)
```

### Расчет времени приготовления
```python
# Обновлена логика в KitchenService
elif new_status == OrderItemStatus.READY:
    item.ready_at = current_time
    # Рассчитываем время приготовления
    if item.preparation_started_at:  # Было: sent_to_kitchen_at
        prep_time = int((current_time - item.preparation_started_at).total_seconds() / 60)
        item.actual_preparation_time = prep_time
```

### Фильтр по умолчанию для кухни
```python
# KitchenService.get_orders_for_department()
if status_filter is None:
    status_filter = [OrderItemStatus.IN_PREPARATION]  # Было: NEW, SENT_TO_KITCHEN, IN_PREPARATION
```

## 📊 Влияние на документацию

### Обновленная документация
- ✅ `KITCHEN_SYSTEM.md` - обновлены рабочие процессы
- ✅ API примеры - обновлены фильтры статусов
- ✅ Модель данных - обновлены значения по умолчанию

### Примеры API
```http
# Получить заказы для цеха (обновлено)
GET /kitchen/orders?department=hot&status_filter=in_preparation,ready

# Вместо старого:
GET /kitchen/orders?department=hot&status_filter=new,sent_to_kitchen
```

## 🚀 Преимущества изменений

### Для кухни:
- **Меньше кликов** - не нужно переводить в статус "готовится"
- **Автоматический таймер** - время приготовления засекается с момента создания
- **Фокус на готовности** - повар сосредотачивается только на готовности блюда

### Для системы:
- **Упрощенная логика** - меньше промежуточных состояний
- **Точная аналитика** - время приготовления считается корректно
- **Меньше ошибок** - меньше ручных переходов между статусами

## 🎯 Результат

Система стала более эффективной:
1. **Упрощен** рабочий процесс кухни
2. **Автоматизирован** учет времени приготовления
3. **Уменьшено** количество ручных операций
4. **Улучшена** точность временных метрик

Кухня теперь может сосредоточиться на приготовлении, а не на управлении статусами! 🍳
