"""
QRes OS 4 - Kitchen Service
Сервис для управления кухонными цехами и позициями заказов
"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
from decimal import Decimal

from ..models import Order, OrderItem, Table, Dish, User
from ..models.order import OrderStatus
from ..models.order_item import OrderItemStatus, KitchenDepartment


class KitchenService:
    """Сервис для работы с кухонными цехами"""
    
    @staticmethod
    async def get_orders_for_department(
        department: KitchenDepartment, 
        db: AsyncSession,
        status_filter: Optional[List[OrderItemStatus]] = None
    ) -> List[Dict]:
        """Получить заказы для конкретного цеха"""
        
        if status_filter is None:
            status_filter = [OrderItemStatus.IN_PREPARATION]
        
        query = select(OrderItem).options(
            joinedload(OrderItem.dish),
            joinedload(OrderItem.order).joinedload(Order.table)
        ).where(
            and_(
                OrderItem.department == department,
                OrderItem.status.in_(status_filter)
            )
        ).order_by(OrderItem.created_at.asc())
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        kitchen_orders = []
        for item in items:
            kitchen_orders.append({
                'id': item.id,
                'order_id': item.order_id,
                'table_number': item.order.table.number if item.order.table else None,
                'dish_name': item.dish.name,
                'dish_image_url': item.dish.main_image_url,
                'quantity': item.quantity,
                'comment': item.comment,
                'status': item.status,
                'department': item.department,
                'estimated_preparation_time': item.estimated_preparation_time,
                'sent_to_kitchen_at': item.sent_to_kitchen_at,
                'created_at': item.created_at
            })
        
        return kitchen_orders
    
    @staticmethod
    async def update_item_status(
        item_id: int,
        new_status: OrderItemStatus,
        db: AsyncSession
    ) -> bool:
        """Обновить статус позиции заказа"""
        
        query = select(OrderItem).options(
            joinedload(OrderItem.order)
        ).where(OrderItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        old_status = item.status
        item.status = new_status
        current_time = datetime.utcnow()
        
        # Устанавливаем временные метки
        if new_status == OrderItemStatus.SENT_TO_KITCHEN:
            item.sent_to_kitchen_at = current_time
        elif new_status == OrderItemStatus.IN_PREPARATION:
            item.preparation_started_at = current_time
        elif new_status == OrderItemStatus.READY:
            item.ready_at = current_time
            # Рассчитываем время приготовления
            if item.preparation_started_at:
                prep_time = int((current_time - item.preparation_started_at).total_seconds() / 60)
                item.actual_preparation_time = prep_time
        elif new_status == OrderItemStatus.SERVED:
            item.served_at = current_time
        
        # Обновляем статус заказа на основе статусов позиций
        await KitchenService._update_order_status(item.order, db)
        
        await db.commit()
        return True
    
    @staticmethod
    async def _update_order_status(order: Order, db: AsyncSession) -> None:
        """Автоматически обновить статус заказа на основе статусов позиций"""
        
        # Получаем все позиции заказа
        query = select(OrderItem).where(OrderItem.order_id == order.id)
        result = await db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return
        
        # Анализируем статусы позиций
        item_statuses = [item.status for item in items]
        
        # Все позиции поданы
        if all(status == OrderItemStatus.SERVED for status in item_statuses):
            if order.status != OrderStatus.SERVED:
                order.status = OrderStatus.SERVED
                order.served_at = datetime.utcnow()
                if order.created_at:
                    order.time_to_serve = int((order.served_at - order.created_at).total_seconds() / 60)
        
        # Есть готовые позиции
        elif any(status == OrderItemStatus.READY for status in item_statuses):
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.READY
        
        # Есть позиции в приготовлении
        elif any(status in [OrderItemStatus.IN_PREPARATION, OrderItemStatus.SENT_TO_KITCHEN] for status in item_statuses):
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.PENDING  # Остается в ожидании
    
    @staticmethod
    async def add_items_to_order(
        order_id: int,
        items_data: List[Dict],
        db: AsyncSession
    ) -> List[OrderItem]:
        """Добавить позиции к существующему заказу"""
        
        # Получаем заказ
        order_query = select(Order).where(Order.id == order_id)
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order:
            raise ValueError("Заказ не найден")
        
        # Проверяем, что заказ можно дополнить
        if order.status not in [OrderStatus.SERVED, OrderStatus.DINING]:
            raise ValueError("Дополнить можно только заказы в статусе SERVED или DINING")
        
        new_items = []
        total_addition = Decimal('0.00')
        
        for item_data in items_data:
            # Получаем блюдо
            dish_query = select(Dish).where(Dish.id == item_data['dish_id'])
            dish_result = await db.execute(dish_query)
            dish = dish_result.scalar_one_or_none()
            
            if not dish or not dish.is_available:
                raise ValueError(f"Блюдо с ID {item_data['dish_id']} недоступно")
            
            # Рассчитываем стоимость
            quantity = item_data['quantity']
            item_total = Decimal(str(dish.price)) * quantity
            total_addition += item_total
            
            # Создаем позицию заказа
            order_item = OrderItem(
                order_id=order.id,
                dish_id=dish.id,
                dish_variation_id=item_data.get('dish_variation_id'),
                quantity=quantity,
                price=Decimal(str(dish.price)),
                total=item_total,
                comment=item_data.get('comment'),
                status=OrderItemStatus.NEW,
                department=dish.department,
                estimated_preparation_time=dish.cooking_time
            )
            
            db.add(order_item)
            new_items.append(order_item)
        
        # Обновляем общую сумму заказа
        order.total_price += total_addition
        
        # Переводим заказ в статус DINING если он был SERVED
        if order.status == OrderStatus.SERVED:
            order.status = OrderStatus.DINING
        
        await db.commit()
        
        # Обновляем позиции с полной информацией
        for item in new_items:
            await db.refresh(item)
        
        return new_items
    
    @staticmethod
    async def get_department_statistics(
        department: KitchenDepartment,
        db: AsyncSession,
        hours: int = 24
    ) -> Dict:
        """Получить статистику по цеху"""
        
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Общее количество позиций
        total_query = select(func.count(OrderItem.id)).where(
            and_(
                OrderItem.department == department,
                OrderItem.created_at >= since_time
            )
        )
        total_result = await db.execute(total_query)
        total_items = total_result.scalar()
        
        # Статистика по статусам
        status_stats = {}
        for status in OrderItemStatus:
            status_query = select(func.count(OrderItem.id)).where(
                and_(
                    OrderItem.department == department,
                    OrderItem.status == status,
                    OrderItem.created_at >= since_time
                )
            )
            status_result = await db.execute(status_query)
            status_stats[f"{status.value}_items"] = status_result.scalar()
        
        # Среднее время приготовления
        avg_time_query = select(func.avg(OrderItem.actual_preparation_time)).where(
            and_(
                OrderItem.department == department,
                OrderItem.actual_preparation_time.is_not(None),
                OrderItem.created_at >= since_time
            )
        )
        avg_time_result = await db.execute(avg_time_query)
        avg_preparation_time = avg_time_result.scalar()
        
        return {
            "department": department.value,
            "total_items": total_items,
            "average_preparation_time": int(avg_preparation_time) if avg_preparation_time else None,
            **status_stats
        }
    
    @staticmethod
    async def send_items_to_kitchen(
        order_id: int,
        item_ids: List[int],
        db: AsyncSession
    ) -> bool:
        """Отправить позиции заказа на кухню"""
        
        query = select(OrderItem).where(
            and_(
                OrderItem.order_id == order_id,
                OrderItem.id.in_(item_ids),
                OrderItem.status == OrderItemStatus.NEW
            )
        )
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        current_time = datetime.utcnow()
        
        for item in items:
            item.status = OrderItemStatus.SENT_TO_KITCHEN
            item.sent_to_kitchen_at = current_time
        
        await db.commit()
        return len(items) > 0
