"""
QRes OS 4 - Orders Router
Роутер для управления заказами и позициями заказов
"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, and_, case
from sqlalchemy.orm import selectinload
from decimal import Decimal

from ..deps import DatabaseSession, WaiterUser, KitchenUser, CurrentUser
from ..models import Order, OrderItem, Table, Dish, User
from ..models.order import OrderStatus, PaymentStatus, OrderType
from ..models.order_item import OrderItemStatus
from ..schemas import (
    Order as OrderSchema, OrderCreate, OrderUpdate, OrderWithDetails,
    OrderItem as OrderItemSchema, OrderItemCreate, OrderItemUpdate, 
    OrderItemWithDish, OrderStatusUpdate, OrderPaymentUpdate, OrderPaymentComplete,
    OrderList, OrderStats, APIResponse, DeliveryOrderCreate, DeliveryOrderResponse
)


def moscow_now() -> datetime:
    """Получить текущее время в московском часовом поясе (UTC+3)"""
    return datetime.utcnow() + timedelta(hours=3)


router = APIRouter()


@router.get("/", response_model=OrderList)
async def get_orders(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    table_id: Optional[int] = Query(None),
    waiter_id: Optional[int] = Query(None)
):
    """
    Получить список заказов с фильтрацией
    """
    query = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.waiter),
        selectinload(Order.payment_method),
        selectinload(Order.items).selectinload(OrderItem.dish)
    )
    
    # Фильтры
    if status is not None:
        query = query.where(Order.status == status)
    if payment_status is not None:
        query = query.where(Order.payment_status == payment_status)
    if table_id is not None:
        query = query.where(Order.table_id == table_id)
    if waiter_id is not None:
        query = query.where(Order.waiter_id == waiter_id)
    
    # Сортировка: сначала активные заказы, потом по времени создания
    query = query.order_by(
        Order.status.in_([OrderStatus.PENDING, OrderStatus.IN_PROGRESS, OrderStatus.READY]).desc(),
        Order.created_at.desc()
    )
    
    # Подсчет общего количества
    count_query = select(func.count(Order.id))
    if status is not None:
        count_query = count_query.where(Order.status == status)
    if payment_status is not None:
        count_query = count_query.where(Order.payment_status == payment_status)
    if table_id is not None:
        count_query = count_query.where(Order.table_id == table_id)
    if waiter_id is not None:
        count_query = count_query.where(Order.waiter_id == waiter_id)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return OrderList(orders=orders, total=total)


@router.post("/", response_model=OrderWithDetails, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Создать новый заказ (для официантов и администраторов)
    """
    try:
        # Проверяем существование столика
        table_query = select(Table).where(Table.id == order_data.table_id)
        table_result = await db.execute(table_query)
        table = table_result.scalar_one_or_none()
        
        if not table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Столик не найден"
            )
        
        if not table.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Столик неактивен"
            )
        
                # Проверяем, есть ли уже активный заказ для этого столика
        # Ищем в порядке приоритета: PENDING -> IN_PROGRESS -> READY -> SERVED -> DINING
        # ВАЖНО: не добавляем к оплаченным заказам!
        existing_order_query = select(Order).where(
            and_(
                Order.table_id == table.id,
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.IN_PROGRESS,
                    OrderStatus.READY,
                    OrderStatus.SERVED,
                    OrderStatus.DINING
                ]),
                Order.payment_status != PaymentStatus.PAID  # НЕ добавляем к уже оплаченным заказам
            )
        ).order_by(
            # Сортируем по приоритету статусов для получения самого подходящего заказа
            case(
                (Order.status == OrderStatus.PENDING, 1),
                (Order.status == OrderStatus.IN_PROGRESS, 2),
                (Order.status == OrderStatus.READY, 3),
                (Order.status == OrderStatus.SERVED, 4),
                (Order.status == OrderStatus.DINING, 5),
                else_=6
            ),
            Order.created_at.desc()  # При равных статусах берем самый новый
        )
        existing_order_result = await db.execute(existing_order_query)
        existing_order = existing_order_result.scalars().first()  # Берем первый по приоритету
        
        if existing_order:
            # ДОБАВЛЕНИЕ К СУЩЕСТВУЮЩЕМУ ЗАКАЗУ
            print(f"🔄 Для столика {table.number} уже есть активный заказ #{existing_order.id}, добавляем к нему позиции")
            
            # Проверяем блюда и рассчитываем стоимость дозаказа
            additional_price = Decimal('0.00')
            validated_items = []
            
            for item_data in order_data.items:
                dish_query = select(Dish).where(Dish.id == item_data.dish_id)
                dish_result = await db.execute(dish_query)
                dish = dish_result.scalar_one_or_none()
                
                if not dish:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Блюдо с ID {item_data.dish_id} не найдено"
                    )
                
                if not dish.is_available:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Блюдо '{dish.name}' недоступно"
                    )
                
                # Получаем вариацию блюда для цены
                from ..models import DishVariation
                
                if hasattr(item_data, 'dish_variation_id') and item_data.dish_variation_id:
                    # Конкретная вариация указана
                    variation_query = select(DishVariation).where(
                        DishVariation.id == item_data.dish_variation_id,
                        DishVariation.dish_id == dish.id,
                        DishVariation.is_available == True
                    )
                    variation_result = await db.execute(variation_query)
                    variation = variation_result.scalar_one_or_none()
                    
                    if not variation:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Вариация блюда с ID {item_data.dish_variation_id} не найдена или недоступна"
                        )
                else:
                    # Берем дефолтную вариацию
                    default_variation_query = select(DishVariation).where(
                        DishVariation.dish_id == dish.id,
                        DishVariation.is_default == True,
                        DishVariation.is_available == True
                    )
                    default_result = await db.execute(default_variation_query)
                    variation = default_result.scalar_one_or_none()
                    
                    if not variation:
                        # Если нет дефолтной, берем первую доступную
                        first_variation_query = select(DishVariation).where(
                            DishVariation.dish_id == dish.id,
                            DishVariation.is_available == True
                        ).limit(1)
                        first_result = await db.execute(first_variation_query)
                        variation = first_result.scalar_one_or_none()
                        
                        if not variation:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"У блюда '{dish.name}' нет доступных вариаций"
                            )
                
                item_total = Decimal(str(variation.price)) * item_data.quantity
                additional_price += item_total
                
                validated_items.append({
                    'dish': dish,
                    'variation': variation,
                    'quantity': item_data.quantity,
                    'price': Decimal(str(variation.price)),
                    'total': item_total,
                    'comment': getattr(item_data, 'comment', None),
                    'department': getattr(dish, 'department', 'kitchen'),
                    'estimated_preparation_time': getattr(dish, 'cooking_time', 15)
                })
            
            # Добавляем позиции к существующему заказу
            order_items = []
            for item_data in validated_items:
                order_item = OrderItem(
                    order_id=existing_order.id,
                    dish_id=item_data['dish'].id,
                    dish_variation_id=item_data['variation'].id,
                    quantity=item_data['quantity'],
                    price=item_data['price'],
                    total=item_data['total'],
                    comment=item_data.get('comment'),
                    status=OrderItemStatus.IN_PREPARATION,
                    department=item_data['department'],
                    estimated_preparation_time=item_data['estimated_preparation_time'],
                    preparation_started_at=moscow_now()
                )
                db.add(order_item)
                order_items.append(order_item)
            
            # Обновляем общую стоимость заказа
            existing_order.total_price = Decimal(str(existing_order.total_price)) + additional_price
            existing_order.updated_at = moscow_now()
            
            await db.commit()
            
            # Загружаем обновленный заказ с полной информацией
            full_order_query = select(Order).options(
                selectinload(Order.table),
                selectinload(Order.waiter),
                selectinload(Order.payment_method),
                selectinload(Order.items).selectinload(OrderItem.dish)
            ).where(Order.id == existing_order.id)
            
            full_order_result = await db.execute(full_order_query)
            full_order = full_order_result.scalar_one()
            
            # Формируем ответ с детальной информацией
            order_response = OrderWithDetails(
                id=full_order.id,
                table_id=full_order.table_id,
                waiter_id=full_order.waiter_id,
                order_type=full_order.order_type,
                notes=full_order.notes,
                kitchen_notes=full_order.kitchen_notes,
                status=full_order.status,
                payment_status=full_order.payment_status,
                payment_method_id=full_order.payment_method_id,
                total_price=full_order.total_price,
                served_at=full_order.served_at,
                cancelled_at=full_order.cancelled_at,
                time_to_serve=full_order.time_to_serve,
                created_at=full_order.created_at,
                updated_at=full_order.updated_at,
                table_number=full_order.table.number if full_order.table else None,
                waiter_name=full_order.waiter.full_name if full_order.waiter else "Не указан",
                payment_method_name=full_order.payment_method.name if full_order.payment_method else None,
                items=[
                    OrderItemWithDish(
                        id=item.id,
                        dish_id=item.dish_id,
                        order_id=item.order_id,
                        quantity=item.quantity,
                        price=item.price,
                        total=item.total,
                        comment=item.comment,
                        status=item.status,
                        department=item.department,
                        created_at=item.created_at,
                        updated_at=item.updated_at,
                        dish_name=item.dish.name if item.dish else "Неизвестное блюдо",
                        dish_image_url=item.dish.main_image_url if item.dish else None,
                        dish_cooking_time=item.dish.cooking_time if item.dish else None,
                        dish_department=item.dish.department if (item.dish and hasattr(item.dish, 'department')) else 'kitchen'
                    )
                    for item in full_order.items
                ]
            )
            
            return order_response
        
        # Проверяем блюда и рассчитываем общую стоимость
        total_price = Decimal('0.00')
        validated_items = []
        
        for item_data in order_data.items:
            dish_query = select(Dish).where(Dish.id == item_data.dish_id)
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            
            if not dish:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Блюдо с ID {item_data.dish_id} не найдено"
                )
            
            if not dish.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Блюдо '{dish.name}' недоступно"
                )
            
            # Получаем вариацию блюда для цены
            from ..models import DishVariation
            
            if hasattr(item_data, 'dish_variation_id') and item_data.dish_variation_id:
                # Конкретная вариация указана
                variation_query = select(DishVariation).where(
                    DishVariation.id == item_data.dish_variation_id,
                    DishVariation.dish_id == dish.id,
                    DishVariation.is_available == True
                )
                variation_result = await db.execute(variation_query)
                variation = variation_result.scalar_one_or_none()
                
                if not variation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Вариация блюда с ID {item_data.dish_variation_id} не найдена или недоступна"
                    )
            else:
                # Берем дефолтную вариацию
                default_variation_query = select(DishVariation).where(
                    DishVariation.dish_id == dish.id,
                    DishVariation.is_default == True,
                    DishVariation.is_available == True
                )
                default_result = await db.execute(default_variation_query)
                variation = default_result.scalar_one_or_none()
                
                if not variation:
                    # Если нет дефолтной, берем первую доступную
                    first_variation_query = select(DishVariation).where(
                        DishVariation.dish_id == dish.id,
                        DishVariation.is_available == True
                    ).limit(1)
                    first_result = await db.execute(first_variation_query)
                    variation = first_result.scalar_one_or_none()
                    
                    if not variation:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"У блюда '{dish.name}' нет доступных вариаций"
                        )
            
            item_total = Decimal(str(variation.price)) * item_data.quantity
            total_price += item_total
            
            validated_items.append({
                'dish': dish,
                'variation': variation,
                'quantity': item_data.quantity,
                'price': Decimal(str(variation.price)),
                'total': item_total,
                'comment': getattr(item_data, 'comment', None),
                'department': getattr(dish, 'department', 'kitchen'),  # Используем department из блюда или по умолчанию 'kitchen'
                'estimated_preparation_time': getattr(dish, 'cooking_time', 15)  # Используем время приготовления из блюда или 15 мин по умолчанию
            })
        
        # Создаем заказ
        new_order = Order(
            table_id=order_data.table_id,
            waiter_id=waiter_user.id,
            order_type=order_data.order_type,
            notes=getattr(order_data, 'notes', None),
            kitchen_notes=getattr(order_data, 'kitchen_notes', None),
            total_price=total_price,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        # Создаем позиции заказа
        order_items = []
        for item_data in validated_items:
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=item_data['dish'].id,
                dish_variation_id=item_data['variation'].id,
                quantity=item_data['quantity'],
                price=item_data['price'],
                total=item_data['total'],
                comment=item_data.get('comment'),
                status=OrderItemStatus.IN_PREPARATION,
                department=item_data['department'],
                estimated_preparation_time=item_data['estimated_preparation_time'],
                preparation_started_at=moscow_now()
            )
            db.add(order_item)
            order_items.append(order_item)
        
        # Обновляем статус столика и привязываем заказ
        table.is_occupied = True
        table.current_order_id = new_order.id
        
        await db.commit()
        
        # Загружаем заказ с полной информацией
        full_order_query = select(Order).options(
            selectinload(Order.table),
            selectinload(Order.waiter),
            selectinload(Order.payment_method),
            selectinload(Order.items).selectinload(OrderItem.dish)
        ).where(Order.id == new_order.id)
        
        full_order_result = await db.execute(full_order_query)
        full_order = full_order_result.scalar_one()
        
        # Формируем ответ с детальной информацией
        order_response = OrderWithDetails(
            id=full_order.id,
            table_id=full_order.table_id,
            waiter_id=full_order.waiter_id,
            order_type=full_order.order_type,
            notes=full_order.notes,
            kitchen_notes=full_order.kitchen_notes,
            status=full_order.status,
            payment_status=full_order.payment_status,
            payment_method_id=full_order.payment_method_id,
            total_price=full_order.total_price,
            served_at=full_order.served_at,
            cancelled_at=full_order.cancelled_at,
            time_to_serve=full_order.time_to_serve,
            created_at=full_order.created_at,
            updated_at=full_order.updated_at,
            table_number=full_order.table.number if full_order.table else None,
            waiter_name=full_order.waiter.full_name if full_order.waiter else "Не указан",
            payment_method_name=full_order.payment_method.name if full_order.payment_method else None,
            items=[
                OrderItemWithDish(
                    id=item.id,
                    dish_id=item.dish_id,
                    order_id=item.order_id,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    comment=item.comment,
                    status=item.status,
                    department=item.department,  # Добавили недостающее поле
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    dish_name=item.dish.name if item.dish else "Неизвестное блюдо",
                    dish_image_url=item.dish.main_image_url if item.dish else None,
                    dish_cooking_time=item.dish.cooking_time if item.dish else None,
                    dish_department=item.dish.department if (item.dish and hasattr(item.dish, 'department')) else 'kitchen'  # Добавили недостающее поле
                )
                for item in full_order.items
            ]
        )
        
        return order_response
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Логируем неожиданные ошибки
        print(f"Error creating order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания заказа: {str(e)}"
        )


@router.get("/active/table/{table_id}", response_model=List[OrderWithDetails])
async def get_active_orders_by_table(
    table_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить активные заказы для указанного столика
    """
    query = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.waiter),
        selectinload(Order.payment_method),
        selectinload(Order.items).selectinload(OrderItem.dish)
    ).where(
        Order.table_id == table_id,
        Order.status.in_([
            OrderStatus.PENDING, 
            OrderStatus.IN_PROGRESS, 
            OrderStatus.READY, 
            OrderStatus.SERVED,
            OrderStatus.DINING
        ])
    )
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    return orders


@router.get("/{order_id}", response_model=OrderWithDetails)
async def get_order(
    order_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о заказе по ID
    """
    query = select(Order).options(
        selectinload(Order.table),
        selectinload(Order.waiter),
        selectinload(Order.payment_method),
        selectinload(Order.items).selectinload(OrderItem.dish)
    ).where(Order.id == order_id)
    
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Формируем ответ с детальной информацией
    order_dict = {k: v for k, v in order.__dict__.items() if k != 'items'}
    order_response = OrderWithDetails(
        **order_dict,
        table_number=order.table.number if order.table else None,
        waiter_name=order.waiter.full_name if order.waiter else "Не указан",
        payment_method_name=order.payment_method.name if order.payment_method else None,
        items=[
            OrderItemWithDish(
                id=item.id,
                dish_id=item.dish_id,
                order_id=item.order_id,
                quantity=item.quantity,
                price=item.price,
                total=item.total,
                comment=item.comment,
                status=item.status,
                department=item.department,  # Добавили недостающее поле
                created_at=item.created_at,
                updated_at=item.updated_at,
                dish_name=item.dish.name if item.dish else "Неизвестное блюдо",
                dish_image_url=item.dish.main_image_url if item.dish else None,
                dish_cooking_time=item.dish.cooking_time if item.dish else None,
                dish_department=item.dish.department if (item.dish and hasattr(item.dish, 'department')) else 'kitchen'  # Добавили недостающее поле
            )
            for item in order.items
        ]
    )
    
    return order_response


@router.patch("/{order_id}/status", response_model=APIResponse)
async def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Обновить статус заказа
    """
    query = select(Order).options(selectinload(Order.table)).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем права на изменение статуса
    if status_data.status == OrderStatus.READY:
        # Кухня может менять статус на "готов"
        if current_user.role.value not in ['kitchen', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только кухня может изменять статус приготовления"
            )
    elif status_data.status == OrderStatus.SERVED:
        # Официанты могут менять статус на "подан"
        if current_user.role.value not in ['waiter', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только официанты могут отмечать заказ как поданный"
            )
    elif status_data.status == OrderStatus.DINING:
        # Официанты могут переводить в статус "клиенты едят"
        if current_user.role.value not in ['waiter', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только официанты могут переводить заказ в статус 'клиенты едят'"
            )
    elif status_data.status == OrderStatus.COMPLETED:
        # Официанты могут завершать заказ
        if current_user.role.value not in ['waiter', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только официанты могут завершать заказ"
            )
    
    old_status = order.status
    order.status = status_data.status
    
    # Обновляем время подачи при смене статуса на "подан"
    if status_data.status == OrderStatus.SERVED and old_status != OrderStatus.SERVED:
        order.served_at = moscow_now()
        order.time_to_serve = int((order.served_at - order.created_at).total_seconds() / 60)
        # Столик НЕ освобождается - клиенты еще едят
    
    # Столик освобождается только при завершении или отмене заказа
    elif status_data.status == OrderStatus.COMPLETED:
        # Освобождаем столик при завершении заказа
        order.completed_at = moscow_now()
        if order.table:
            order.table.is_occupied = False
            order.table.current_order_id = None
    
    # При отмене заказа также освобождаем столик
    elif status_data.status == OrderStatus.CANCELLED:
        order.cancelled_at = moscow_now()
        if order.table:
            order.table.is_occupied = False
            order.table.current_order_id = None
    
    await db.commit()
    
    status_names = {
        OrderStatus.PENDING: "ожидает",
        OrderStatus.READY: "готов",
        OrderStatus.SERVED: "подан",
        OrderStatus.DINING: "клиенты едят",
        OrderStatus.COMPLETED: "завершен",
        OrderStatus.CANCELLED: "отменен"
    }
    
    return APIResponse(
        message=f"Статус заказа #{order.id} изменен: {status_names[status_data.status]}"
    )


@router.patch("/{order_id}/payment", response_model=APIResponse)
async def update_order_payment_status(
    order_id: int,
    payment_data: OrderPaymentUpdate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Обновить статус оплаты заказа (для официантов и администраторов)
    """
    query = select(Order).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем способ оплаты если он указан
    if payment_data.payment_method_id:
        from ..models import PaymentMethod
        payment_method_query = select(PaymentMethod).where(
            PaymentMethod.id == payment_data.payment_method_id,
            PaymentMethod.is_active == True
        )
        payment_method_result = await db.execute(payment_method_query)
        payment_method = payment_method_result.scalar_one_or_none()
        
        if not payment_method:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Способ оплаты не найден или неактивен"
            )
        
        order.payment_method_id = payment_data.payment_method_id
    
    # ВАЖНО: Если пытаемся оплатить заказ, проверяем готовность всех позиций
    if payment_data.payment_status == PaymentStatus.PAID:
        unfinished_items_query = select(OrderItem).where(
            and_(
                OrderItem.order_id == order_id,
                OrderItem.status.in_([
                    OrderItemStatus.IN_PREPARATION,
                    OrderItemStatus.READY
                ])
            )
        )
        unfinished_items_result = await db.execute(unfinished_items_query)
        unfinished_items = unfinished_items_result.scalars().all()
        
        if unfinished_items:
            unfinished_names = []
            for item in unfinished_items:
                # Загружаем блюдо для получения названия
                dish_query = select(Dish).where(Dish.id == item.dish_id)
                dish_result = await db.execute(dish_query)
                dish = dish_result.scalar_one_or_none()
                dish_name = dish.name if dish else f"Блюдо ID {item.dish_id}"
                unfinished_names.append(f"{dish_name} (статус: {item.status.value})")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя закрыть заказ: не все позиции готовы. Неготовые позиции: {'; '.join(unfinished_names)}"
            )
    
    order.payment_status = payment_data.payment_status
    
    # Если заказ оплачен, освобождаем столик
    if payment_data.payment_status == PaymentStatus.PAID:
        if order.table_id:
            # Загружаем столик с заказом
            table_query = select(Table).where(Table.id == order.table_id)
            table_result = await db.execute(table_query)
            table = table_result.scalar_one_or_none()
            
            if table:
                table.is_occupied = False
                table.current_order_id = None
    
    await db.commit()
    
    payment_names = {
        PaymentStatus.UNPAID: "не оплачен",
        PaymentStatus.PAID: "оплачен",
        PaymentStatus.REFUNDED: "возврат"
    }
    
    return APIResponse(
        message=f"Статус оплаты заказа #{order.id}: {payment_names[payment_data.payment_status]}"
    )


@router.post("/{order_id}/complete-payment", response_model=APIResponse)
async def complete_order_payment(
    order_id: int,
    payment_data: OrderPaymentComplete,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Завершить оплату заказа с указанием способа оплаты
    """
    query = select(Order).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    if order.payment_status == PaymentStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заказ уже оплачен"
        )
    
    # ВАЖНО: Проверяем, что все позиции заказа готовы
    unfinished_items_query = select(OrderItem).where(
        and_(
            OrderItem.order_id == order_id,
            OrderItem.status.in_([
                OrderItemStatus.IN_PREPARATION,
                OrderItemStatus.READY
            ])
        )
    )
    unfinished_items_result = await db.execute(unfinished_items_query)
    unfinished_items = unfinished_items_result.scalars().all()
    
    if unfinished_items:
        unfinished_names = []
        for item in unfinished_items:
            # Загружаем блюдо для получения названия
            dish_query = select(Dish).where(Dish.id == item.dish_id)
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            dish_name = dish.name if dish else f"Блюдо ID {item.dish_id}"
            unfinished_names.append(f"{dish_name} (статус: {item.status.value})")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя закрыть заказ: не все позиции готовы. Неготовые позиции: {'; '.join(unfinished_names)}"
        )
    
    # Проверяем способ оплаты
    from ..models import PaymentMethod
    payment_method_query = select(PaymentMethod).where(
        PaymentMethod.id == payment_data.payment_method_id,
        PaymentMethod.is_active == True
    )
    payment_method_result = await db.execute(payment_method_query)
    payment_method = payment_method_result.scalar_one_or_none()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден или неактивен"
        )
    
    # Обновляем заказ
    order.payment_method_id = payment_data.payment_method_id
    order.payment_status = payment_data.payment_status
    
    # Если заказ оплачен, освобождаем столик
    if payment_data.payment_status == PaymentStatus.PAID:
        if order.table_id:
            # Загружаем столик с заказом
            table_query = select(Table).where(Table.id == order.table_id)
            table_result = await db.execute(table_query)
            table = table_result.scalar_one_or_none()
            
            if table:
                table.is_occupied = False
                table.current_order_id = None
    
    await db.commit()
    
    return APIResponse(
        message=f"Заказ #{order.id} успешно оплачен способом '{payment_method.name}'"
    )


@router.get("/stats/summary", response_model=OrderStats)
async def get_order_stats(
    db: DatabaseSession,
    current_user: CurrentUser,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None)
):
    """
    Получить статистику по заказам
    """
    base_query = select(Order)
    
    # Фильтр по датам
    if date_from:
        base_query = base_query.where(Order.created_at >= date_from)
    if date_to:
        base_query = base_query.where(Order.created_at <= date_to)
    
    # Общее количество заказов
    total_orders_query = select(func.count(Order.id))
    if date_from:
        total_orders_query = total_orders_query.where(Order.created_at >= date_from)
    if date_to:
        total_orders_query = total_orders_query.where(Order.created_at <= date_to)
    
    total_orders_result = await db.execute(total_orders_query)
    total_orders = total_orders_result.scalar()
    
    # Заказы по статусам
    status_queries = {}
    for status in OrderStatus:
        status_query = select(func.count(Order.id)).where(Order.status == status)
        if date_from:
            status_query = status_query.where(Order.created_at >= date_from)
        if date_to:
            status_query = status_query.where(Order.created_at <= date_to)
        
        status_result = await db.execute(status_query)
        status_queries[status.value + '_orders'] = status_result.scalar()
    
    # Общая выручка и средний чек
    revenue_query = select(func.sum(Order.total_price)).where(Order.payment_status == PaymentStatus.PAID)
    if date_from:
        revenue_query = revenue_query.where(Order.created_at >= date_from)
    if date_to:
        revenue_query = revenue_query.where(Order.created_at <= date_to)
    
    revenue_result = await db.execute(revenue_query)
    total_revenue = revenue_result.scalar() or Decimal('0.00')
    
    # Среднее время приготовления
    avg_time_query = select(func.avg(Order.time_to_serve)).where(Order.time_to_serve.isnot(None))
    if date_from:
        avg_time_query = avg_time_query.where(Order.created_at >= date_from)
    if date_to:
        avg_time_query = avg_time_query.where(Order.created_at <= date_to)
    
    avg_time_result = await db.execute(avg_time_query)
    avg_cooking_time = avg_time_result.scalar()
    
    # Средний чек
    paid_orders_count = status_queries.get('paid_orders', 0)
    average_order_value = total_revenue / paid_orders_count if paid_orders_count > 0 else Decimal('0.00')
    
    return OrderStats(
        total_orders=total_orders,
        pending_orders=status_queries.get('pending_orders', 0),
        in_progress_orders=status_queries.get('in_progress_orders', 0),
        ready_orders=status_queries.get('ready_orders', 0),
        served_orders=status_queries.get('served_orders', 0),
        cancelled_orders=status_queries.get('cancelled_orders', 0),
        total_revenue=total_revenue,
        average_order_value=average_order_value,
        average_cooking_time=int(avg_cooking_time) if avg_cooking_time else None
    )


@router.post("/delivery", response_model=DeliveryOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_delivery_order(
    order_data: DeliveryOrderCreate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Создать новый заказ с доставкой (для официантов и администраторов)
    """
    try:
        # Для доставки не нужен столик, но проверяем блюда
        total_price = Decimal('0.00')
        validated_items = []
        
        for item_data in order_data.items:
            dish_query = select(Dish).where(Dish.id == item_data.dish_id)
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            
            if not dish:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Блюдо с ID {item_data.dish_id} не найдено"
                )
            
            if not dish.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Блюдо '{dish.name}' недоступно"
                )
            
            # Получаем вариацию блюда для цены
            from ..models import DishVariation
            
            if hasattr(item_data, 'dish_variation_id') and item_data.dish_variation_id:
                # Конкретная вариация указана
                variation_query = select(DishVariation).where(
                    DishVariation.id == item_data.dish_variation_id,
                    DishVariation.dish_id == dish.id,
                    DishVariation.is_available == True
                )
                variation_result = await db.execute(variation_query)
                variation = variation_result.scalar_one_or_none()
                
                if not variation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Вариация блюда с ID {item_data.dish_variation_id} не найдена или недоступна"
                    )
            else:
                # Берем дефолтную вариацию
                default_variation_query = select(DishVariation).where(
                    DishVariation.dish_id == dish.id,
                    DishVariation.is_default == True,
                    DishVariation.is_available == True
                )
                default_result = await db.execute(default_variation_query)
                variation = default_result.scalar_one_or_none()
                
                if not variation:
                    # Если нет дефолтной, берем первую доступную
                    first_variation_query = select(DishVariation).where(
                        DishVariation.dish_id == dish.id,
                        DishVariation.is_available == True
                    ).limit(1)
                    first_result = await db.execute(first_variation_query)
                    variation = first_result.scalar_one_or_none()
                    
                    if not variation:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"У блюда '{dish.name}' нет доступных вариаций"
                        )
            
            item_total = Decimal(str(variation.price)) * item_data.quantity
            total_price += item_total
            
            validated_items.append({
                'dish': dish,
                'variation': variation,
                'quantity': item_data.quantity,
                'price': Decimal(str(variation.price)),
                'total': item_total,
                'comment': getattr(item_data, 'comment', None),
                'department': getattr(dish, 'department', 'kitchen'),  # Используем department из блюда или по умолчанию 'kitchen'
                'estimated_preparation_time': getattr(dish, 'cooking_time', 15)  # Используем время приготовления из блюда или 15 мин по умолчанию
            })
        
        # Создаем заказ с доставкой
        new_order = Order(
            table_id=None,  # Для доставки столик не нужен
            waiter_id=waiter_user.id,
            order_type=OrderType.DELIVERY,
            notes=order_data.notes,
            kitchen_notes=order_data.kitchen_notes,
            total_price=total_price,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
            # Данные клиента для доставки
            customer_name=order_data.customer_name,
            customer_phone=order_data.customer_phone,
            delivery_address=order_data.delivery_address,
            delivery_notes=order_data.delivery_notes
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        # Создаем позиции заказа
        order_items = []
        for item_data in validated_items:
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=item_data['dish'].id,
                dish_variation_id=item_data['variation'].id,
                quantity=item_data['quantity'],
                price=item_data['price'],
                total=item_data['total'],
                comment=item_data.get('comment'),
                status=OrderItemStatus.IN_PREPARATION,
                department=item_data['department'],
                estimated_preparation_time=item_data['estimated_preparation_time'],
                preparation_started_at=moscow_now()
            )
            db.add(order_item)
            order_items.append(order_item)
        
        await db.commit()
        
        # Загружаем заказ с полной информацией
        full_order_query = select(Order).options(
            selectinload(Order.waiter),
            selectinload(Order.items).selectinload(OrderItem.dish)
        ).where(Order.id == new_order.id)
        
        full_order_result = await db.execute(full_order_query)
        full_order = full_order_result.scalar_one()
        
        # Формируем ответ с детальной информацией
        order_response = DeliveryOrderResponse(
            id=full_order.id,
            waiter_id=full_order.waiter_id,
            order_type=full_order.order_type,
            status=full_order.status,
            payment_status=full_order.payment_status,
            total_price=full_order.total_price,
            notes=full_order.notes,
            kitchen_notes=full_order.kitchen_notes,
            customer_name=full_order.customer_name,
            customer_phone=full_order.customer_phone,
            delivery_address=full_order.delivery_address,
            delivery_notes=full_order.delivery_notes,
            served_at=full_order.served_at,
            cancelled_at=full_order.cancelled_at,
            time_to_serve=full_order.time_to_serve,
            created_at=full_order.created_at,
            updated_at=full_order.updated_at,
            waiter_name=full_order.waiter.full_name if full_order.waiter else "Не указан",
            items=[
                OrderItemWithDish(
                    id=item.id,
                    dish_id=item.dish_id,
                    order_id=item.order_id,
                    quantity=item.quantity,
                    price=item.price,
                    total=item.total,
                    comment=item.comment,
                    status=item.status,
                    department=item.department,  # Добавили недостающее поле
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    dish_name=item.dish.name if item.dish else "Неизвестное блюдо",
                    dish_image_url=item.dish.main_image_url if item.dish else None,
                    dish_cooking_time=item.dish.cooking_time if item.dish else None,
                    dish_department=item.dish.department if (item.dish and hasattr(item.dish, 'department')) else 'kitchen'  # Добавили недостающее поле
                )
                for item in full_order.items
            ]
        )
        
        return order_response
        
    except HTTPException:
        # Перебрасываем HTTP исключения как есть
        raise
    except Exception as e:
        # Логируем неожиданные ошибки
        print(f"Error creating delivery order: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания заказа с доставкой: {str(e)}"
        )


@router.delete("/{order_id}", response_model=APIResponse)
async def cancel_order(
    order_id: int,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Отменить заказ (для официантов и администраторов)
    """
    query = select(Order).options(selectinload(Order.table)).where(Order.id == order_id)
    result = await db.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    if order.status in [OrderStatus.SERVED, OrderStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя отменить уже поданный или отмененный заказ"
        )
    
    # Отменяем заказ
    order.status = OrderStatus.CANCELLED
    order.cancelled_at = moscow_now()
    
    # Освобождаем столик
    order.table.is_occupied = False
    order.table.current_order_id = None
    
    await db.commit()
    
    return APIResponse(
        message=f"Заказ #{order.id} отменен"
    )
