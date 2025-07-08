"""
QRes OS 4 - Locations Router
Роутер для управления локациями/зонами ресторана
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..deps import DatabaseSession, AdminUser, CurrentUser
from ..models import Location, Table
from ..schemas import (
    Location as LocationSchema, LocationCreate, LocationUpdate,
    LocationWithTables, LocationList, APIResponse
)
from ..services.locations import (
    sync_tables_with_location_status,
    check_location_has_active_orders,
    bulk_update_tables_status
)
from ..services.data_integrity import check_data_integrity, auto_fix_integrity_issues


router = APIRouter()


@router.get("/", response_model=LocationList)
async def get_locations(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None)
):
    """
    Получить список локаций с фильтрацией
    """
    query = select(Location)
    
    # Фильтры
    if is_active is not None:
        query = query.where(Location.is_active == is_active)
    
    # Сортировка по названию
    query = query.order_by(Location.name)
    
    # Получение общего количества
    count_query = select(func.count(Location.id))
    if is_active is not None:
        count_query = count_query.where(Location.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return LocationList(locations=locations, total=total)

@router.get("/admin/integrity-check", response_model=dict)
async def check_locations_integrity(
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Проверка целостности данных локаций и столиков (только для администраторов)
    """
    integrity_report = await check_data_integrity(db)
    return integrity_report


@router.post("/admin/auto-fix", response_model=dict)
async def auto_fix_locations_integrity(
    db: DatabaseSession,
    admin_user: AdminUser,
    dry_run: bool = Query(True, description="Предварительный просмотр без применения изменений"),
    fix_types: List[str] = Query(None, description="Типы проблем для исправления")
):
    """
    Автоматическое исправление проблем целостности (только для администраторов)
    """
    fix_result = await auto_fix_integrity_issues(
        db=db,
        fix_types=fix_types,
        dry_run=dry_run
    )
    return fix_result


@router.post("/", response_model=LocationSchema)
async def create_location(
    location_data: LocationCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новую локацию (только для администраторов)
    """
    # Проверяем уникальность названия
    existing_query = select(Location).where(Location.name == location_data.name)
    existing_result = await db.execute(existing_query)
    existing_location = existing_result.scalar_one_or_none()
    
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Локация с названием '{location_data.name}' уже существует"
        )
    
    # Создаем локацию
    new_location = Location(
        name=location_data.name,
        description=location_data.description,
        color=location_data.color,
        is_active=location_data.is_active
    )
    
    db.add(new_location)
    await db.commit()
    await db.refresh(new_location)
    
    return new_location


@router.get("/{location_id}", response_model=LocationWithTables)
async def get_location(
    location_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о локации по ID
    """
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )
    
    # Подсчитываем количество столиков в локации
    tables_count_query = select(func.count(Table.id)).where(Table.location_id == location_id)
    tables_count_result = await db.execute(tables_count_query)
    tables_count = tables_count_result.scalar()
    
    # Преобразуем в схему с количеством столиков
    location_dict = {
        "id": location.id,
        "name": location.name,
        "description": location.description,
        "color": location.color,
        "is_active": location.is_active,
        "created_at": location.created_at,
        "updated_at": location.updated_at,
        "tables_count": tables_count
    }
    
    return LocationWithTables(**location_dict)


@router.patch("/{location_id}", response_model=LocationSchema)
async def update_location(
    location_id: int,
    location_data: LocationUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию о локации (только для администраторов)
    """
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )
    
    # Проверяем уникальность названия (если изменяется)
    if location_data.name and location_data.name != location.name:
        existing_query = select(Location).where(Location.name == location_data.name)
        existing_result = await db.execute(existing_query)
        existing_location = existing_result.scalar_one_or_none()
        
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Локация с названием '{location_data.name}' уже существует"
            )
    
    # Сохраняем текущий статус для проверки изменений
    old_is_active = location.is_active
    
    # Если локация деактивируется, проверяем активные заказы
    if 'is_active' in location_data.model_dump(exclude_unset=True):
        new_is_active = location_data.is_active
        
        if old_is_active and not new_is_active:
            # Проверяем наличие активных заказов
            has_active_orders, active_orders_count = await check_location_has_active_orders(db, location_id)
            
            if has_active_orders:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Нельзя деактивировать локацию с активными заказами. "
                           f"Найдено столиков с заказами: {active_orders_count}"
                )
    
    # Обновляем поля локации
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    await db.commit()
    await db.refresh(location)
    
    # Синхронизируем статус столиков, если изменился статус активности
    if 'is_active' in update_data and update_data['is_active'] != old_is_active:
        affected_tables = await sync_tables_with_location_status(
            db=db,
            location_id=location_id,
            location_is_active=update_data['is_active'],
            force_sync=False  # Не принудительно активируем столики при активации локации
        )
        
        if affected_tables:
            # Обновляем объект локации после синхронизации
            await db.refresh(location)
    
    return location


@router.patch("/{location_id}/sync-tables", response_model=APIResponse)
async def sync_location_tables(
    location_id: int,
    db: DatabaseSession,
    admin_user: AdminUser,
    force_activation: bool = Query(False, description="Принудительно активировать столики при активной локации")
):
    """
    Принудительная синхронизация статуса столиков с локацией (только для администраторов)
    """
    # Проверяем существование локации
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )
    
    # Выполняем синхронизацию
    affected_tables = await sync_tables_with_location_status(
        db=db,
        location_id=location_id,
        location_is_active=location.is_active,
        force_sync=force_activation
    )
    
    if not affected_tables:
        return APIResponse(
            message=f"Все столики в локации '{location.name}' уже синхронизированы"
        )
    
    return APIResponse(
        message=f"Синхронизированы столики в локации '{location.name}'. "
                f"Изменено столиков: {len(affected_tables)}"
    )


@router.get("/{location_id}/tables")
async def get_location_tables(
    location_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Получить список столиков в локации
    """
    # Проверяем существование локации
    location_query = select(Location).where(Location.id == location_id)
    location_result = await db.execute(location_query)
    location = location_result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )
    
    # Получаем столики
    tables_query = select(Table).where(Table.location_id == location_id).order_by(Table.number)
    tables_query = tables_query.offset(skip).limit(limit)
    tables_result = await db.execute(tables_query)
    tables = tables_result.scalars().all()
    
    # Получаем общее количество
    count_query = select(func.count(Table.id)).where(Table.location_id == location_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return {
        "tables": tables,
        "total": total,
        "location": location
    }


@router.delete("/{location_id}", response_model=APIResponse)
async def delete_location(
    location_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить или деактивировать локацию (только для администраторов)
    """
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Локация не найдена"
        )
    
    # Проверяем, есть ли столики в локации
    tables_query = select(func.count(Table.id)).where(Table.location_id == location_id)
    tables_result = await db.execute(tables_query)
    tables_count = tables_result.scalar()
    
    if tables_count > 0:
        # Деактивируем вместо удаления
        location.is_active = False
        await db.commit()
        
        return APIResponse(
            message=f"Локация '{location.name}' деактивирована (содержит {tables_count} столиков)"
        )
    else:
        # Полное удаление, если нет столиков
        await db.delete(location)
        await db.commit()
        
        return APIResponse(
            message=f"Локация '{location.name}' удалена"
        )
