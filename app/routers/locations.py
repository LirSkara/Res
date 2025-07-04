"""
QRes OS 4 - Locations Router
Роутер для управления локациями/зонами ресторана
"""
from typing import Optional
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
    
    # Обновляем поля
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    await db.commit()
    await db.refresh(location)
    
    return location


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
