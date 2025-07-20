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
from ..deps import moscow_now


def moscow_now() -> datetime:
    """Получить текущее время в московском часовом поясе (UTC+3)"""
    return datetime.utcnow() + timedelta(hours=3)


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
            joinedload(OrderItem.order),
            joinedload(OrderItem.dish)
        ).where(OrderItem.id == item_id)
        
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            return False
        
        old_status = item.status
        item.status = new_status
        current_time = datetime.utcnow()
        
        # Устанавливаем временные метки
        if new_status == OrderItemStatus.IN_PREPARATION:
            # Если еще не было установлено время начала приготовления
            if not item.preparation_started_at:
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
        
        # Получаем все позиции заказа с данными о блюдах
        query = select(OrderItem).options(
            joinedload(OrderItem.dish)
        ).where(OrderItem.order_id == order.id)
        result = await db.execute(query)
        items = result.scalars().all()
        
        if not items:
            return
        
        # Анализируем статусы позиций
        item_statuses = [item.status for item in items]
        old_status = order.status
        
        # Все позиции поданы
        if all(status == OrderItemStatus.SERVED for status in item_statuses):
            if order.status != OrderStatus.SERVED:
                order.status = OrderStatus.SERVED
                order.served_at = datetime.utcnow()
                if order.created_at:
                    order.time_to_serve = int((order.served_at - order.created_at).total_seconds() / 60)
        
        # Все позиции готовы (но еще не поданы)
        elif all(status in [OrderItemStatus.READY, OrderItemStatus.SERVED] for status in item_statuses) and \
             any(status == OrderItemStatus.READY for status in item_statuses):
            if order.status != OrderStatus.READY:
                order.status = OrderStatus.READY
        
        # Есть хотя бы одна готовая позиция (частично готов)
        elif any(status == OrderItemStatus.READY for status in item_statuses):
            # Если заказ был в ожидании, переводим в частично готовый
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.READY
        
        # Есть позиции в приготовлении
        elif any(status == OrderItemStatus.IN_PREPARATION for status in item_statuses):
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.PENDING  # Остается в ожидании
        
        # Логируем изменение статуса для отладки
        if old_status != order.status:
            print(f"🔄 Заказ #{order.id}: статус изменен с {old_status.value} на {order.status.value}")
            
            # Подсчитываем готовые позиции для уведомления
            ready_items = [item for item in items if item.status == OrderItemStatus.READY]
            total_items = len(items)
            
            print(f"   📊 Готовых позиций: {len(ready_items)}/{total_items}")
            
            # Если есть готовые позиции, выводим их список
            if ready_items:
                ready_names = [item.dish.name if item.dish else f"Позиция #{item.id}" for item in ready_items]
                print(f"   ✅ Готовые блюда: {', '.join(ready_names)}")
            
            # Позиции еще в приготовлении
            in_prep_items = [item for item in items if item.status == OrderItemStatus.IN_PREPARATION]
            if in_prep_items:
                prep_names = [item.dish.name if item.dish else f"Позиция #{item.id}" for item in in_prep_items]
                print(f"   🔥 Готовятся: {', '.join(prep_names)}")
                
        # TODO: Здесь можно добавить отправку WebSocket уведомлений официантам
    
    @staticmethod
    async def get_order_progress(order_id: int, db: AsyncSession) -> Dict:
        """Получить прогресс выполнения заказа"""
        
        # Получаем заказ с позициями и данными о блюдах
        query = select(Order).options(
            selectinload(Order.items).selectinload(OrderItem.dish)
        ).where(Order.id == order_id)
        
        result = await db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            return None
        
        items = order.items
        if not items:
            return {
                "order_id": order_id,
                "total_items": 0,
                "ready_items": 0,
                "in_preparation_items": 0,
                "served_items": 0,
                "progress_percentage": 0,
                "items_detail": []
            }
        
        # Анализируем статусы позиций
        total_items = len(items)
        ready_items = len([item for item in items if item.status == OrderItemStatus.READY])
        in_prep_items = len([item for item in items if item.status == OrderItemStatus.IN_PREPARATION])
        served_items = len([item for item in items if item.status == OrderItemStatus.SERVED])
        
        # Рассчитываем прогресс (готовые + поданные / общее количество)
        completed_items = ready_items + served_items
        progress_percentage = int((completed_items / total_items) * 100) if total_items > 0 else 0
        
        # Детальная информация по позициям
        items_detail = []
        for item in items:
            items_detail.append({
                "id": item.id,
                "dish_name": item.dish.name if item.dish else f"Позиция #{item.id}",
                "quantity": item.quantity,
                "status": item.status.value,
                "preparation_started_at": item.preparation_started_at.isoformat() if item.preparation_started_at else None,
                "ready_at": item.ready_at.isoformat() if item.ready_at else None,
                "served_at": item.served_at.isoformat() if item.served_at else None,
                "estimated_time": item.estimated_preparation_time,
                "actual_time": item.actual_preparation_time
            })
        
        return {
            "order_id": order_id,
            "order_status": order.status.value,
            "total_items": total_items,
            "ready_items": ready_items,
            "in_preparation_items": in_prep_items,
            "served_items": served_items,
            "progress_percentage": progress_percentage,
            "items_detail": items_detail,
            "all_ready": ready_items == total_items and served_items == 0,  # Все готово, но не подано
            "partially_ready": ready_items > 0 and ready_items < total_items,  # Частично готово
            "fully_served": served_items == total_items  # Все подано
        }
    
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
        
        # Проверяем, что заказ можно дополнить (исключаем только завершенные и отмененные заказы)
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise ValueError("Нельзя дополнить завершенный или отмененный заказ")
        
        # Если заказ в статусе PENDING, переводим его в IN_PROGRESS
        if order.status == OrderStatus.PENDING:
            order.status = OrderStatus.IN_PROGRESS
        
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
                status=OrderItemStatus.IN_PREPARATION,
                department=dish.department,
                estimated_preparation_time=dish.cooking_time,
                preparation_started_at=moscow_now()
            )
            
            db.add(order_item)
            new_items.append(order_item)
        
        # Обновляем общую сумму заказа
        order.total_price += total_addition
        
        # Обновляем статус заказа в зависимости от текущего статуса
        if order.status == OrderStatus.SERVED:
            # Если заказ был подан, но добавили новые позиции - переводим в DINING
            order.status = OrderStatus.DINING
        elif order.status == OrderStatus.READY:
            # Если заказ был готов, но добавили новые позиции - возвращаем в IN_PROGRESS
            order.status = OrderStatus.IN_PROGRESS
        elif order.status in [OrderStatus.DINING, OrderStatus.IN_PROGRESS, OrderStatus.PENDING]:
            # Оставляем текущий статус, но убеждаемся что это не PENDING
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.IN_PROGRESS
        
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
        """
        DEPRECATED: Функция больше не используется.
        Все позиции теперь создаются сразу со статусом IN_PREPARATION.
        """
        # Все позиции уже в статусе IN_PREPARATION, ничего делать не нужно
        return True

    @staticmethod
    async def get_all_kitchen_dishes(
        db: AsyncSession,
        department: Optional[KitchenDepartment] = None,
        status_filter: Optional[List[OrderItemStatus]] = None
    ) -> List[Dict]:
        """Получить все блюда для кухни из всех заказов"""
        
        # Если фильтр статусов не указан, показываем активные статусы
        if status_filter is None:
            status_filter = [
                OrderItemStatus.IN_PREPARATION,
                OrderItemStatus.READY,
                OrderItemStatus.SERVED
            ]
        
        # Строим базовый запрос
        query = select(OrderItem).options(
            joinedload(OrderItem.dish),
            joinedload(OrderItem.order).joinedload(Order.table)
        ).where(
            OrderItem.status.in_(status_filter)
        )
        
        # Добавляем фильтр по цеху, если указан
        if department:
            query = query.where(OrderItem.department == department)
        
        # Сортируем по времени создания (старые первыми)
        query = query.order_by(OrderItem.created_at.asc())
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        kitchen_dishes = []
        for item in items:
            # Вычисляем время в готовке, если блюдо готовится
            preparation_time = None
            if item.status == OrderItemStatus.IN_PREPARATION and item.preparation_started_at:
                time_diff = moscow_now() - item.preparation_started_at
                preparation_time = int(time_diff.total_seconds() / 60)  # в минутах
            
            # Вычисляем фактическое время готовки, если блюдо готово
            actual_time = None
            if item.ready_at and item.preparation_started_at:
                time_diff = item.ready_at - item.preparation_started_at
                actual_time = int(time_diff.total_seconds() / 60)  # в минутах
            
            kitchen_dishes.append({
                'id': item.id,
                'order_id': item.order_id,
                'dish_name': item.dish.name,
                'quantity': item.quantity,
                'status': item.status.value,
                'department': item.department.value,
                'comment': item.comment,
                'estimated_preparation_time': item.dish.cooking_time,
                'actual_preparation_time': actual_time,
                'preparation_started_at': item.preparation_started_at.isoformat() if item.preparation_started_at else None,
                'ready_at': item.ready_at.isoformat() if item.ready_at else None,
                'served_at': item.served_at.isoformat() if item.served_at else None,
                'created_at': item.order.created_at.isoformat(),  # Используем время создания заказа, а не элемента
                'table_number': item.order.table.number if item.order.table else None,
                'current_preparation_time': preparation_time
            })
        
        return kitchen_dishes
