"""
QRes OS 4 - Location Services
Сервисы для работы с локациями
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models import Location, Table, Order
from ..logger import get_logger

logger = get_logger(__name__)


async def sync_tables_with_location_status(
    db: AsyncSession,
    location_id: int,
    location_is_active: bool,
    force_sync: bool = False
) -> List[int]:
    """
    Синхронизирует статус всех столиков с статусом локации
    
    Args:
        db: Сессия базы данных
        location_id: ID локации
        location_is_active: Новый статус активности локации
        force_sync: Принудительная синхронизация (для активации столиков)
    
    Returns:
        List[int]: Список ID столиков, которые были изменены
    """
    affected_table_ids = []
    
    # Получаем все столики локации
    query = select(Table).where(Table.location_id == location_id)
    result = await db.execute(query)
    tables = result.scalars().all()
    
    if not tables:
        logger.info(f"В локации {location_id} нет столиков для синхронизации")
        return affected_table_ids
    
    for table in tables:
        table_changed = False
        
        if not location_is_active:
            # Если локация деактивируется - деактивируем все столики
            if table.is_active:
                logger.info(f"Деактивация столика {table.number} (ID: {table.id}) из-за деактивации локации {location_id}")
                table.is_active = False
                table_changed = True
            
            # Сбрасываем статус занятости и текущий заказ
            if table.is_occupied:
                logger.info(f"Освобождение столика {table.number} (ID: {table.id}) из-за деактивации локации")
                table.is_occupied = False
                table_changed = True
            
            if table.current_order_id:
                logger.warning(f"Сброс текущего заказа столика {table.number} (ID: {table.id}) из-за деактивации локации")
                table.current_order_id = None
                table_changed = True
        
        elif location_is_active and force_sync:
            # Если локация активируется и включена принудительная синхронизация
            # активируем только неактивные столики без активных заказов
            if not table.is_active and not table.current_order_id:
                logger.info(f"Активация столика {table.number} (ID: {table.id}) из-за активации локации {location_id}")
                table.is_active = True
                table_changed = True
        
        if table_changed:
            affected_table_ids.append(table.id)
    
    # Сохраняем изменения
    if affected_table_ids:
        await db.commit()
        logger.info(f"Синхронизация завершена. Изменено столиков: {len(affected_table_ids)}")
    
    return affected_table_ids


async def get_location_with_active_orders(
    db: AsyncSession,
    location_id: int
) -> Optional[Location]:
    """
    Получает локацию с информацией об активных заказах в её столиках
    
    Args:
        db: Сессия базы данных
        location_id: ID локации
    
    Returns:
        Location или None, если не найдена
    """
    query = (
        select(Location)
        .options(
            selectinload(Location.tables)
            .selectinload(Table.current_order)
        )
        .where(Location.id == location_id)
    )
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def check_location_has_active_orders(
    db: AsyncSession,
    location_id: int
) -> tuple[bool, int]:
    """
    Проверяет, есть ли в локации активные заказы
    
    Args:
        db: Сессия базы данных
        location_id: ID локации
    
    Returns:
        tuple[bool, int]: (есть_активные_заказы, количество_активных_заказов)
    """
    # Подсчитываем столики с активными заказами в данной локации
    query = (
        select(Table)
        .where(
            Table.location_id == location_id,
            Table.current_order_id.isnot(None)
        )
    )
    
    result = await db.execute(query)
    tables_with_orders = result.scalars().all()
    
    active_orders_count = len(tables_with_orders)
    has_active_orders = active_orders_count > 0
    
    if has_active_orders:
        logger.warning(f"В локации {location_id} найдено {active_orders_count} столиков с активными заказами")
    
    return has_active_orders, active_orders_count


async def bulk_update_tables_status(
    db: AsyncSession,
    location_id: int,
    is_active: bool,
    force_occupied_reset: bool = False
) -> int:
    """
    Массовое обновление статуса столиков в локации
    
    Args:
        db: Сессия базы данных
        location_id: ID локации
        is_active: Новый статус активности
        force_occupied_reset: Принудительно сбросить статус занятости
    
    Returns:
        int: Количество обновленных столиков
    """
    # Базовые поля для обновления
    update_data = {"is_active": is_active}
    
    # Если деактивируем или принудительно сбрасываем
    if not is_active or force_occupied_reset:
        update_data.update({
            "is_occupied": False,
            "current_order_id": None
        })
    
    # Выполняем массовое обновление
    stmt = (
        update(Table)
        .where(Table.location_id == location_id)
        .values(**update_data)
    )
    
    result = await db.execute(stmt)
    affected_rows = result.rowcount
    
    await db.commit()
    
    logger.info(f"Массовое обновление: {affected_rows} столиков в локации {location_id}")
    
    return affected_rows
