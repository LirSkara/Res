"""
Роутер для статистики дашборда
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.models import User, Order, Table, Location, Category, Dish, Ingredient, PaymentMethod
from app.schemas import APIResponse
from app.deps import get_current_user, RoleChecker
from app.models.user import UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=APIResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN]))
):
    """
    Получить статистику для дашборда
    """
    
    # Получаем количество пользователей
    total_users_query = select(func.count(User.id)).where(User.is_active == True)
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0
    
    # Получаем количество заказов за сегодня
    from datetime import datetime, date
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    total_orders_query = select(func.count(Order.id)).where(
        Order.created_at >= today_start,
        Order.created_at <= today_end
    )
    total_orders_result = await db.execute(total_orders_query)
    total_orders = total_orders_result.scalar() or 0
    
    # Получаем выручку за сегодня
    from app.models.order import PaymentStatus
    revenue_query = select(func.sum(Order.total_price)).where(
        Order.payment_status == PaymentStatus.PAID,
        Order.created_at >= today_start,
        Order.created_at <= today_end
    )
    revenue_result = await db.execute(revenue_query)
    total_revenue = float(revenue_result.scalar() or 0)
    
    # Получаем количество активных столов
    active_tables_query = select(func.count(Table.id)).where(
        Table.is_active == True
    )
    active_tables_result = await db.execute(active_tables_query)
    active_tables = active_tables_result.scalar() or 0
    
    # Получаем количество локаций
    total_locations_query = select(func.count(Location.id)).where(Location.is_active == True)
    total_locations_result = await db.execute(total_locations_query)
    total_locations = total_locations_result.scalar() or 0
    
    # Получаем количество категорий
    total_categories_query = select(func.count(Category.id)).where(Category.is_active == True)
    total_categories_result = await db.execute(total_categories_query)
    total_categories = total_categories_result.scalar() or 0
    
    # Получаем количество блюд
    total_dishes_query = select(func.count(Dish.id)).where(Dish.is_available == True)
    total_dishes_result = await db.execute(total_dishes_query)
    total_dishes = total_dishes_result.scalar() or 0
    
    # Получаем количество ингредиентов
    total_ingredients_query = select(func.count(Ingredient.id))
    total_ingredients_result = await db.execute(total_ingredients_query)
    total_ingredients = total_ingredients_result.scalar() or 0
    
    # Получаем количество способов оплаты
    total_payment_methods_query = select(func.count(PaymentMethod.id)).where(PaymentMethod.is_active == True)
    total_payment_methods_result = await db.execute(total_payment_methods_query)
    total_payment_methods = total_payment_methods_result.scalar() or 0
    
    stats_data = {
        "totalUsers": total_users,
        "totalOrders": total_orders,
        "totalRevenue": total_revenue,
        "activeTables": active_tables,
        "totalLocations": total_locations,
        "totalCategories": total_categories,
        "totalDishes": total_dishes,
        "totalIngredients": total_ingredients,
        "totalPaymentMethods": total_payment_methods
    }
    
    return APIResponse(
        success=True,
        data=stats_data,
        message="Статистика дашборда получена успешно"
    )
