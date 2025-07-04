"""
QRes OS 4 - Order Items Router
Роутер для управления позициями заказов (отдельный файл согласно ТЗ)
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from decimal import Decimal

from ..deps import DatabaseSession, WaiterUser, KitchenUser, CurrentUser
from ..models import OrderItem, Order, Dish
from ..models.order_item import OrderItemStatus
from ..schemas import (
    OrderItem as OrderItemSchema, OrderItemCreate, OrderItemUpdate, 
    OrderItemWithDish, OrderItemStatusUpdate, APIResponse
)


router = APIRouter()


@router.post("/{order_id}/items/", response_model=OrderItemWithDish, status_code=status.HTTP_201_CREATED)
async def add_item_to_order(
    order_id: int,
    item_data: OrderItemCreate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Добавить блюдо в заказ
    """
    # Проверяем существование заказа
    order_query = select(Order).where(Order.id == order_id)
    order_result = await db.execute(order_query)
    order = order_result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем права доступа (официант может редактировать только свои заказы)
    if waiter_user.role.value == "waiter" and order.waiter_id != waiter_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете редактировать только свои заказы"
        )
    
    # Проверяем блюдо
    dish_query = select(Dish).where(Dish.id == item_data.dish_id)
    dish_result = await db.execute(dish_query)
    dish = dish_result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    if not dish.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Блюдо недоступно"
        )
    
    # Создаем новую позицию
    item_total = Decimal(str(dish.price)) * item_data.quantity
    
    new_item = OrderItem(
        order_id=order_id,
        dish_id=item_data.dish_id,
        quantity=item_data.quantity,
        price=Decimal(str(dish.price)),
        total=item_total,
        comment=item_data.comment,
        status=OrderItemStatus.NEW
    )
    
    db.add(new_item)
    
    # Обновляем общую стоимость заказа
    order.total_price += item_total
    
    await db.commit()
    await db.refresh(new_item)
    
    # Загружаем позицию с информацией о блюде
    item_query = select(OrderItem).options(
        selectinload(OrderItem.dish)
    ).where(OrderItem.id == new_item.id)
    
    item_result = await db.execute(item_query)
    item_with_dish = item_result.scalar_one()
    
    # Формируем ответ
    return OrderItemWithDish(
        **item_with_dish.__dict__,
        dish_name=item_with_dish.dish.name,
        dish_image_url=item_with_dish.dish.image_url,
        dish_cooking_time=item_with_dish.dish.cooking_time
    )


@router.patch("/{order_id}/items/{item_id}", response_model=OrderItemWithDish)
async def update_order_item(
    order_id: int,
    item_id: int,
    item_data: OrderItemUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Обновить позицию в заказе
    """
    # Загружаем позицию с заказом и блюдом
    item_query = select(OrderItem).options(
        selectinload(OrderItem.order),
        selectinload(OrderItem.dish)
    ).where(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id
    )
    
    item_result = await db.execute(item_query)
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция заказа не найдена"
        )
    
    # Проверяем права доступа
    if (current_user.role.value == "waiter" and 
        item.order.waiter_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете редактировать только свои заказы"
        )
    
    # Сохраняем старую стоимость для обновления общей суммы заказа
    old_total = item.total
    
    # Обновляем поля
    update_data = item_data.model_dump(exclude_unset=True)
    
    if "quantity" in update_data:
        item.quantity = update_data["quantity"]
        item.total = item.price * item.quantity
    
    if "comment" in update_data:
        item.comment = update_data["comment"]
    
    if "status" in update_data:
        item.status = update_data["status"]
    
    # Обновляем общую стоимость заказа
    if item.total != old_total:
        item.order.total_price += (item.total - old_total)
    
    await db.commit()
    await db.refresh(item)
    
    # Формируем ответ
    return OrderItemWithDish(
        **item.__dict__,
        dish_name=item.dish.name,
        dish_image_url=item.dish.image_url,
        dish_cooking_time=item.dish.cooking_time
    )


@router.patch("/{order_id}/items/{item_id}/status", response_model=APIResponse)
async def update_item_status(
    order_id: int,
    item_id: int,
    status_data: OrderItemStatusUpdate,
    db: DatabaseSession,
    kitchen_user: KitchenUser
):
    """
    Обновить статус позиции заказа (для кухни)
    """
    # Загружаем позицию
    item_query = select(OrderItem).where(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id
    )
    
    item_result = await db.execute(item_query)
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция заказа не найдена"
        )
    
    # Обновляем статус
    item.status = status_data.status
    
    await db.commit()
    
    return APIResponse(
        success=True,
        message=f"Статус позиции обновлён на '{status_data.status.value}'"
    )


@router.delete("/{order_id}/items/{item_id}", response_model=APIResponse)
async def remove_item_from_order(
    order_id: int,
    item_id: int,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Удалить блюдо из заказа
    """
    # Загружаем позицию с заказом
    item_query = select(OrderItem).options(
        selectinload(OrderItem.order)
    ).where(
        OrderItem.id == item_id,
        OrderItem.order_id == order_id
    )
    
    item_result = await db.execute(item_query)
    item = item_result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция заказа не найдена"
        )
    
    # Проверяем права доступа
    if (waiter_user.role.value == "waiter" and 
        item.order.waiter_id != waiter_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Вы можете удалять позиции только из своих заказов"
        )
    
    # Обновляем общую стоимость заказа
    item.order.total_price -= item.total
    
    # Удаляем позицию
    await db.delete(item)
    await db.commit()
    
    return APIResponse(
        success=True,
        message="Позиция удалена из заказа"
    )
