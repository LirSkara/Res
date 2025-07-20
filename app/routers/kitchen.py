"""
QRes OS 4 - Kitchen Router
Роутер для управления кухонными цехами
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..deps import DatabaseSession, CurrentUser
from ..models.order_item import OrderItemStatus, KitchenDepartment
from ..schemas.order_item import KitchenOrderItem, OrderItemStatusUpdate, OrderItemCreate
from ..schemas.common import APIResponse
from ..services.kitchen import KitchenService


router = APIRouter(prefix="/kitchen", tags=["kitchen"])


@router.get("/orders", response_model=List[KitchenOrderItem])
async def get_kitchen_orders(
    department: KitchenDepartment,
    db: DatabaseSession,
    current_user: CurrentUser,
    status_filter: Optional[List[OrderItemStatus]] = Query(None)
):
    """
    Получить заказы для конкретного цеха
    """
    # Проверяем права доступа
    if current_user.role.value not in ['kitchen', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для кухни и администраторов"
        )
    
    orders = await KitchenService.get_orders_for_department(
        department=department,
        db=db,
        status_filter=status_filter
    )
    
    return [KitchenOrderItem(**order) for order in orders]


@router.patch("/items/{item_id}/status", response_model=APIResponse)
async def update_item_status(
    item_id: int,
    status_data: OrderItemStatusUpdate,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Обновить статус позиции заказа
    """
    # Проверяем права доступа
    if current_user.role.value not in ['kitchen', 'admin', 'waiter', 'KITCHEN', 'ADMIN', 'WAITER']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ для кухни, официантов и администраторов"
        )
    
    success = await KitchenService.update_item_status(
        item_id=item_id,
        new_status=status_data.status,
        db=db
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция заказа не найдена"
        )
    
    status_names = {
        OrderItemStatus.IN_PREPARATION: "готовится",
        OrderItemStatus.READY: "готова",
        OrderItemStatus.SERVED: "подана",
        OrderItemStatus.CANCELLED: "отменена"
    }
    
    return APIResponse(
        message=f"Статус позиции #{item_id} изменен: {status_names[status_data.status]}"
    )


@router.post("/orders/{order_id}/items", response_model=APIResponse)
async def add_items_to_order(
    order_id: int,
    items: List[OrderItemCreate],
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Добавить позиции к существующему заказу
    """
    # Проверяем права доступа
    if current_user.role.value not in ['waiter', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для официантов и администраторов"
        )
    
    try:
        items_data = [item.dict() for item in items]
        new_items = await KitchenService.add_items_to_order(
            order_id=order_id,
            items_data=items_data,
            db=db
        )
        
        return APIResponse(
            message=f"Добавлено {len(new_items)} позиций к заказу #{order_id}"
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/orders/{order_id}/send-to-kitchen", response_model=APIResponse)
async def send_items_to_kitchen(
    order_id: int,
    item_ids: List[int],
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    DEPRECATED: Отправить позиции заказа на кухню
    
    Этот эндпоинт больше не выполняет никаких действий,
    так как все позиции теперь создаются сразу со статусом IN_PREPARATION.
    """
    # Проверяем права доступа
    if current_user.role.value not in ['waiter', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для официантов и администраторов"
        )
    
    # Функция больше не нужна, все позиции сразу в приготовлении
    success = await KitchenService.send_items_to_kitchen(
        order_id=order_id,
        item_ids=item_ids,
        db=db
    )
    
    return APIResponse(
        message=f"Все позиции уже находятся на кухне (статус IN_PREPARATION)"
    )


@router.get("/departments/{department}/stats")
async def get_department_stats(
    department: KitchenDepartment,
    db: DatabaseSession,
    current_user: CurrentUser,
    hours: int = Query(24, ge=1, le=168)  # от 1 часа до недели
):
    """
    Получить статистику по цеху
    """
    # Проверяем права доступа
    if current_user.role.value not in ['kitchen', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для кухни и администраторов"
        )
    
    stats = await KitchenService.get_department_statistics(
        department=department,
        db=db,
        hours=hours
    )
    
    return stats


@router.get("/departments")
async def get_departments(current_user: CurrentUser):
    """
    Получить список всех кухонных цехов
    """
    departments = []
    for dept in KitchenDepartment:
        departments.append({
            "value": dept.value,
            "name": {
                "bar": "Бар",
                "cold": "Холодный цех",
                "hot": "Горячий цех", 
                "dessert": "Кондитерский цех",
                "grill": "Гриль",
                "bakery": "Выпечка"
            }.get(dept.value, dept.value)
        })
    
    return departments


@router.get("/orders/{order_id}/progress")
async def get_order_progress(
    order_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить прогресс выполнения заказа
    """
    progress = await KitchenService.get_order_progress(order_id, db)
    
    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    return progress


@router.get("/dishes", response_model=List[KitchenOrderItem])
async def get_all_kitchen_dishes(
    db: DatabaseSession,
    current_user: CurrentUser,
    department: Optional[KitchenDepartment] = Query(None),
    status_filter: Optional[List[OrderItemStatus]] = Query(None)
):
    """
    Получить все блюда для кухни (из всех заказов)
    """
    # Проверяем права доступа
    if current_user.role.value not in ['kitchen', 'admin', 'KITCHEN', 'ADMIN']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для кухни и администраторов"
        )
    
    dishes = await KitchenService.get_all_kitchen_dishes(
        db=db,
        department=department,
        status_filter=status_filter
    )
    
    return dishes
