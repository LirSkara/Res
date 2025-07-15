"""
QRes OS 4 - Orders Service
Бизнес-логика для работы с заказами (согласно ТЗ)
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from decimal import Decimal
from datetime import datetime

from ..models import Order, OrderItem, Table, Dish, User
from ..models.order import OrderStatus, PaymentStatus
from ..models.order_item import OrderItemStatus


class OrderService:
    """Сервис для работы с заказами"""
    
    @staticmethod
    async def calculate_order_total(order_items: List[dict], db: AsyncSession) -> Decimal:
        """Рассчитать общую стоимость заказа"""
        total = Decimal('0.00')
        
        for item in order_items:
            dish_query = select(Dish).where(Dish.id == item['dish_id'])
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            
            if dish and dish.is_available:
                item_total = Decimal(str(dish.price)) * item['quantity']
                total += item_total
        
        return total
    
    @staticmethod
    async def validate_order_items(order_items: List[dict], db: AsyncSession) -> List[dict]:
        """Валидация и подготовка позиций заказа"""
        validated_items = []
        
        for item in order_items:
            dish_query = select(Dish).where(Dish.id == item['dish_id'])
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            
            if not dish:
                raise ValueError(f"Блюдо с ID {item['dish_id']} не найдено")
            
            if not dish.is_available:
                raise ValueError(f"Блюдо '{dish.name}' недоступно")
            
            item_total = Decimal(str(dish.price)) * item['quantity']
            
            validated_items.append({
                'dish': dish,
                'quantity': item['quantity'],
                'price': Decimal(str(dish.price)),
                'total': item_total,
                'comment': item.get('comment'),
                'department': dish.department,
                'estimated_preparation_time': dish.cooking_time
            })
        
        return validated_items
    
    @staticmethod
    async def check_table_availability(table_id: int, db: AsyncSession) -> bool:
        """Проверить доступность столика"""
        table_query = select(Table).where(Table.id == table_id)
        table_result = await db.execute(table_query)
        table = table_result.scalar_one_or_none()
        
        if not table:
            raise ValueError("Столик не найден")
        
        if not table.is_active:
            raise ValueError("Столик неактивен")
        
        # Проверяем, нет ли уже активного заказа
        existing_order_query = select(Order).where(
            Order.table_id == table_id,
            Order.status.in_([OrderStatus.PENDING, OrderStatus.READY, OrderStatus.SERVED, OrderStatus.DINING])
        )
        existing_order_result = await db.execute(existing_order_query)
        existing_order = existing_order_result.scalar_one_or_none()
        
        if existing_order:
            raise ValueError(f"У столика {table.number} уже есть активный заказ #{existing_order.id}")
        
        return True
    
    @staticmethod
    async def get_order_statistics(db: AsyncSession) -> dict:
        """Получить статистику заказов"""
        # Общее количество заказов
        total_query = select(func.count(Order.id))
        total_result = await db.execute(total_query)
        total_orders = total_result.scalar()
        
        # Статистика по статусам
        status_stats = {}
        for status in OrderStatus:
            status_query = select(func.count(Order.id)).where(Order.status == status)
            status_result = await db.execute(status_query)
            status_stats[f"{status.value}_orders"] = status_result.scalar()
        
        # Общая выручка (только оплаченные заказы)
        revenue_query = select(func.sum(Order.total_price)).where(
            Order.payment_status == PaymentStatus.PAID
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or Decimal('0.00')
        
        # Средний чек
        avg_order_query = select(func.avg(Order.total_price)).where(
            Order.payment_status == PaymentStatus.PAID
        )
        avg_order_result = await db.execute(avg_order_query)
        avg_order_value = avg_order_result.scalar() or Decimal('0.00')
        
        return {
            "total_orders": total_orders,
            **status_stats,
            "total_revenue": total_revenue,
            "average_order_value": avg_order_value
        }
    
    @staticmethod
    async def mark_order_as_served(order_id: int, db: AsyncSession) -> bool:
        """Отметить заказ как поданный"""
        order_query = select(Order).where(Order.id == order_id)
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            return False
        
        order.status = OrderStatus.SERVED
        order.served_at = datetime.utcnow()
        
        # Рассчитываем время подачи
        if order.created_at:
            time_diff = order.served_at - order.created_at
            order.time_to_serve = int(time_diff.total_seconds() / 60)  # в минутах
        
        await db.commit()
        return True
    
    @staticmethod
    async def cancel_order(order_id: int, db: AsyncSession) -> bool:
        """Отменить заказ"""
        order_query = select(Order).options(
            selectinload(Order.table)
        ).where(Order.id == order_id)
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            return False
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()
        
        # Освобождаем столик
        if order.table:
            order.table.is_occupied = False
            order.table.current_order_id = None
        
        await db.commit()
        return True
