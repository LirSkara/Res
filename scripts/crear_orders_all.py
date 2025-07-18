#!/usr/bin/env python3
"""
Скрипт для очистки всех заказов из базы данных
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models import Order, OrderItem, Table
from sqlalchemy import select, delete


async def clear_orders():
    """Очищает все заказы и освобождает столики"""
    async with AsyncSessionLocal() as db:
        try:
            # Удаляем все элементы заказов
            order_items_result = await db.execute(select(OrderItem))
            order_items_count = len(order_items_result.fetchall())
            
            await db.execute(delete(OrderItem))
            print(f'Удалено {order_items_count} элементов заказов')
            
            # Удаляем все заказы
            orders_result = await db.execute(select(Order))
            orders_count = len(orders_result.fetchall())
            
            await db.execute(delete(Order))
            print(f'Удалено {orders_count} заказов')
            
            # Освобождаем все столики
            tables_result = await db.execute(select(Table))
            tables = tables_result.scalars().all()
            
            freed_count = 0
            for table in tables:
                if table.is_occupied or table.current_order_id:
                    table.is_occupied = False
                    table.current_order_id = None
                    freed_count += 1
            
            print(f'Освобождено {freed_count} столиков')
            
            # Сохраняем изменения
            await db.commit()
            print('✅ База данных очищена от заказов')
            
        except Exception as e:
            await db.rollback()
            print(f'❌ Ошибка очистки: {e}')
            raise


if __name__ == "__main__":
    asyncio.run(clear_orders())
