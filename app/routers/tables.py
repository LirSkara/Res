"""
QRes OS 4 - Tables Router
Роутер для управления столиками
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid

from ..deps import DatabaseSession, AdminUser, WaiterUser, CurrentUser
from ..models import Table, Location, Order
from ..schemas import (
    Table as TableSchema, TableCreate, TableUpdate, TableStatusUpdate,
    TableWithLocation, TableList, QRCodeResponse, APIResponse
)
from ..config import settings
from ..services.locations import check_location_has_active_orders


router = APIRouter()


@router.get("/", response_model=TableList)
async def get_tables(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    location_id: Optional[int] = Query(None),
    is_occupied: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None)
):
    """
    Получить список столиков с фильтрацией
    """
    query = select(Table).options(selectinload(Table.location_obj))
    
    # Фильтры
    if location_id is not None:
        query = query.where(Table.location_id == location_id)
    if is_occupied is not None:
        query = query.where(Table.is_occupied == is_occupied)
    if is_active is not None:
        query = query.where(Table.is_active == is_active)
    
    # Сортировка по номеру столика
    query = query.order_by(Table.number)
    
    # Получение общего количества
    count_query = select(func.count(Table.id))
    if location_id is not None:
        count_query = count_query.where(Table.location_id == location_id)
    if is_occupied is not None:
        count_query = count_query.where(Table.is_occupied == is_occupied)
    if is_active is not None:
        count_query = count_query.where(Table.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tables = result.scalars().all()
    
    return TableList(tables=tables, total=total)


@router.post("/", response_model=TableSchema)
async def create_table(
    table_data: TableCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новый столик (только для администраторов)
    """
    # Проверяем, не занят ли номер столика
    existing_query = select(Table).where(Table.number == table_data.number)
    existing_result = await db.execute(existing_query)
    existing_table = existing_result.scalar_one_or_none()
    
    if existing_table:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Столик с номером {table_data.number} уже существует"
        )
    
    # Проверяем существование локации
    if table_data.location_id:
        location_query = select(Location).where(Location.id == table_data.location_id)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанная локация не найдена"
            )
        
        # ВАЖНО: Нельзя создать активный столик в неактивной локации
        if not location.is_active and table_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя создать активный столик в неактивной локации '{location.name}'"
            )
    
    # Если локация не указана, но столик должен быть активным - предупреждаем
    elif table_data.is_active and not table_data.location_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Активный столик должен быть привязан к локации"
        )
    
    # Создаем столик с уникальным QR-кодом
    new_table = Table(
        number=table_data.number,
        seats=table_data.seats,
        location_id=table_data.location_id,
        description=table_data.description,
        is_active=table_data.is_active,
        qr_code=str(uuid.uuid4())
    )
    
    db.add(new_table)
    await db.commit()
    await db.refresh(new_table)
    
    return new_table


@router.get("/{table_id}", response_model=TableSchema)
async def get_table(
    table_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о столике по ID
    """
    query = select(Table).options(selectinload(Table.location_obj)).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    return table


@router.patch("/{table_id}", response_model=TableSchema)
async def update_table(
    table_id: int,
    table_data: TableUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию о столике (только для администраторов)
    """
    query = select(Table).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    # Проверяем номер столика на уникальность (если изменяется)
    if table_data.number and table_data.number != table.number:
        existing_query = select(Table).where(Table.number == table_data.number)
        existing_result = await db.execute(existing_query)
        existing_table = existing_result.scalar_one_or_none()
        
        if existing_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Столик с номером {table_data.number} уже существует"
            )
    
    # Проверяем существование локации (если изменяется)
    if table_data.location_id:
        location_query = select(Location).where(Location.id == table_data.location_id)
        location_result = await db.execute(location_query)
        location = location_result.scalar_one_or_none()
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанная локация не найдена"
            )
        
        # ВАЖНО: Нельзя активировать столик в неактивной локации
        if not location.is_active and table_data.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нельзя активировать столик в неактивной локации '{location.name}'"
            )
    
    # Дополнительная проверка: если активируется столик, проверяем его текущую локацию
    if table_data.is_active and not table_data.location_id:
        # Проверяем текущую локацию столика
        if table.location_id:
            current_location_query = select(Location).where(Location.id == table.location_id)
            current_location_result = await db.execute(current_location_query)
            current_location = current_location_result.scalar_one_or_none()
            
            if current_location and not current_location.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Нельзя активировать столик в неактивной локации"
                )
    
    # Обновляем поля
    update_data = table_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(table, field, value)
    
    # ВАЖНО: Если столик деактивируется, автоматически сбрасываем статус занятости
    if 'is_active' in update_data and not update_data['is_active']:
        table.is_occupied = False
        table.current_order_id = None
    
    await db.commit()
    await db.refresh(table)
    
    return table


@router.patch("/{table_id}/status", response_model=APIResponse)
async def update_table_status(
    table_id: int,
    status_data: TableStatusUpdate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Изменить статус занятости столика (для официантов и администраторов)
    """
    query = select(Table).options(selectinload(Table.location_obj)).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
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
    
    # Проверяем статус локации
    if table.location_obj and not table.location_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя изменить статус столика в неактивной локации '{table.location_obj.name}'"
        )
    
    table.is_occupied = status_data.is_occupied
    await db.commit()
    
    status_text = "занят" if status_data.is_occupied else "свободен"
    location_info = f" в локации '{table.location_obj.name}'" if table.location_obj else ""
    
    return APIResponse(
        message=f"Статус столика {table.number}{location_info} изменен: {status_text}"
    )


@router.get("/{table_id}/qr", response_model=QRCodeResponse)
async def get_table_qr_info(
    table_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о QR-коде столика
    """
    query = select(Table).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    menu_url = f"{settings.qr_base_url}?table={table.qr_code}"
    qr_url = f"/api/qr/{table.qr_code}"
    
    return QRCodeResponse(
        qr_code=table.qr_code,
        qr_url=qr_url,
        menu_url=menu_url
    )


@router.get("/{table_id}/sync-status", response_model=dict)
async def get_table_sync_status(
    table_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Проверить статус синхронизации столика с его локацией
    """
    query = select(Table).options(selectinload(Table.location_obj)).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    sync_status = {
        "table_id": table.id,
        "table_number": table.number,
        "table_is_active": table.is_active,
        "location_id": table.location_id,
        "location_name": table.location_obj.name if table.location_obj else None,
        "location_is_active": table.location_obj.is_active if table.location_obj else None,
        "is_synchronized": True,
        "sync_issues": []
    }
    
    # Проверяем различные проблемы синхронизации
    if table.location_obj:
        # Проверка: активный столик в неактивной локации
        if table.is_active and not table.location_obj.is_active:
            sync_status["is_synchronized"] = False
            sync_status["sync_issues"].append(
                "Столик активен, но находится в неактивной локации"
            )
        
        # Проверка: столик с заказом в неактивной локации
        if table.current_order_id and not table.location_obj.is_active:
            sync_status["is_synchronized"] = False
            sync_status["sync_issues"].append(
                "У столика есть активный заказ, но локация неактивна"
            )
    else:
        # Столик без локации
        if table.is_active:
            sync_status["is_synchronized"] = False
            sync_status["sync_issues"].append(
                "Активный столик не привязан к локации"
            )
    
    return sync_status


@router.patch("/{table_id}/force-sync", response_model=APIResponse)
async def force_sync_table_with_location(
    table_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Принудительная синхронизация столика с его локацией (только для администраторов)
    """
    query = select(Table).options(selectinload(Table.location_obj)).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    changes = []
    
    if table.location_obj:
        # Синхронизируем с локацией
        if table.is_active and not table.location_obj.is_active:
            table.is_active = False
            table.is_occupied = False
            table.current_order_id = None
            changes.append("деактивирован")
            changes.append("освобожден")
            if table.current_order_id:
                changes.append("сброшен активный заказ")
    else:
        # Столик без локации - деактивируем если активен
        if table.is_active:
            table.is_active = False
            table.is_occupied = False
            table.current_order_id = None
            changes.append("деактивирован (нет локации)")
    
    if changes:
        await db.commit()
        return APIResponse(
            message=f"Столик {table.number} синхронизирован: {', '.join(changes)}"
        )
    else:
        return APIResponse(
            message=f"Столик {table.number} уже синхронизирован с локацией"
        )


@router.delete("/{table_id}", response_model=APIResponse)
async def delete_table(
    table_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить или деактивировать столик (только для администраторов)
    """
    query = select(Table).options(selectinload(Table.location_obj)).where(Table.id == table_id)
    result = await db.execute(query)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Столик не найден"
        )
    
    # Проверяем, есть ли активные заказы
    if table.current_order_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить столик {table.number} с активным заказом (ID: {table.current_order_id})"
        )
    
    # Деактивируем вместо удаления и сбрасываем все статусы
    table.is_active = False
    table.is_occupied = False
    table.current_order_id = None
    
    await db.commit()
    
    location_info = f" в локации '{table.location_obj.name}'" if table.location_obj else ""
    
    return APIResponse(
        message=f"Столик {table.number}{location_info} деактивирован"
    )
