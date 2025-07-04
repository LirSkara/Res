"""
QRes OS 4 - Payment Methods Router
Роутер для управления способами оплаты
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..deps import DatabaseSession, AdminUser, CurrentUser
from ..models import PaymentMethod
from ..schemas import (
    PaymentMethod as PaymentMethodSchema, PaymentMethodCreate, PaymentMethodUpdate,
    PaymentMethodList, APIResponse
)


router = APIRouter()


@router.get("/", response_model=PaymentMethodList)
async def get_payment_methods(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None)
):
    """
    Получить список способов оплаты
    """
    query = select(PaymentMethod)
    
    # Фильтры
    if is_active is not None:
        query = query.where(PaymentMethod.is_active == is_active)
    
    # Сортировка по названию
    query = query.order_by(PaymentMethod.name)
    
    # Получение общего количества
    count_query = select(func.count(PaymentMethod.id))
    if is_active is not None:
        count_query = count_query.where(PaymentMethod.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    payment_methods = result.scalars().all()
    
    return PaymentMethodList(payment_methods=payment_methods, total=total)


@router.get("/active")
async def get_active_payment_methods(
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить список активных способов оплаты
    """
    query = select(PaymentMethod).where(PaymentMethod.is_active == True).order_by(PaymentMethod.name)
    result = await db.execute(query)
    payment_methods = result.scalars().all()
    
    return {
        "payment_methods": payment_methods,
        "total": len(payment_methods)
    }


@router.post("/", response_model=PaymentMethodSchema)
async def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новый способ оплаты (только для администраторов)
    """
    # Проверяем уникальность названия
    existing_query = select(PaymentMethod).where(PaymentMethod.name == payment_method_data.name)
    existing_result = await db.execute(existing_query)
    existing_method = existing_result.scalar_one_or_none()
    
    if existing_method:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Способ оплаты с названием '{payment_method_data.name}' уже существует"
        )
    
    # Создаем способ оплаты
    new_payment_method = PaymentMethod(
        name=payment_method_data.name,
        is_active=payment_method_data.is_active
    )
    
    db.add(new_payment_method)
    await db.commit()
    await db.refresh(new_payment_method)
    
    return new_payment_method


@router.get("/{payment_method_id}", response_model=PaymentMethodSchema)
async def get_payment_method(
    payment_method_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о способе оплаты по ID
    """
    query = select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    result = await db.execute(query)
    payment_method = result.scalar_one_or_none()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден"
        )
    
    return payment_method


@router.patch("/{payment_method_id}", response_model=PaymentMethodSchema)
async def update_payment_method(
    payment_method_id: int,
    payment_method_data: PaymentMethodUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию о способе оплаты (только для администраторов)
    """
    query = select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    result = await db.execute(query)
    payment_method = result.scalar_one_or_none()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден"
        )
    
    # Проверяем уникальность названия (если изменяется)
    if payment_method_data.name and payment_method_data.name != payment_method.name:
        existing_query = select(PaymentMethod).where(PaymentMethod.name == payment_method_data.name)
        existing_result = await db.execute(existing_query)
        existing_method = existing_result.scalar_one_or_none()
        
        if existing_method:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Способ оплаты с названием '{payment_method_data.name}' уже существует"
            )
    
    # Обновляем поля
    update_data = payment_method_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment_method, field, value)
    
    await db.commit()
    await db.refresh(payment_method)
    
    return payment_method


@router.delete("/{payment_method_id}", response_model=APIResponse)
async def delete_payment_method(
    payment_method_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить или деактивировать способ оплаты (только для администраторов)
    """
    query = select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    result = await db.execute(query)
    payment_method = result.scalar_one_or_none()
    
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Способ оплаты не найден"
        )
    
    # В реальном приложении следует проверить, используется ли способ оплаты в заказах
    # Деактивируем вместо удаления для сохранения истории
    payment_method.is_active = False
    await db.commit()
    
    return APIResponse(
        message=f"Способ оплаты '{payment_method.name}' деактивирован"
    )
