"""
QRes OS 4 - Dishes Service
Бизнес-логика для работы с блюдами (согласно ТЗ)
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from decimal import Decimal

from ..models import Dish, Category, OrderItem


class DishService:
    """Сервис для работы с блюдами"""
    
    @staticmethod
    async def get_popular_dishes(db: AsyncSession, limit: int = 10) -> List[Dish]:
        """Получить популярные блюда"""
        popular_query = select(
            Dish,
            func.sum(OrderItem.quantity).label('total_orders')
        ).join(
            OrderItem, Dish.id == OrderItem.dish_id
        ).group_by(
            Dish.id
        ).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit)
        
        result = await db.execute(popular_query)
        dishes = [row[0] for row in result.all()]
        return dishes
    
    @staticmethod
    async def get_dishes_by_category(db: AsyncSession, category_id: int) -> List[Dish]:
        """Получить блюда по категории"""
        query = select(Dish).options(
            selectinload(Dish.category_obj)
        ).where(
            Dish.category_id == category_id,
            Dish.is_available == True
        ).order_by(Dish.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def search_dishes(db: AsyncSession, search_term: str) -> List[Dish]:
        """Поиск блюд по названию или описанию"""
        query = select(Dish).where(
            (Dish.name.ilike(f"%{search_term}%")) |
            (Dish.description.ilike(f"%{search_term}%")) |
            (Dish.ingredients.ilike(f"%{search_term}%"))
        ).where(
            Dish.is_available == True
        ).order_by(Dish.name)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_dish_statistics(db: AsyncSession, dish_id: int) -> dict:
        """Получить статистику по блюду"""
        dish_query = select(Dish).where(Dish.id == dish_id)
        dish_result = await db.execute(dish_query)
        dish = dish_result.scalar_one_or_none()
        
        if not dish:
            return {}
        
        # Количество заказов блюда
        orders_query = select(func.sum(OrderItem.quantity)).where(
            OrderItem.dish_id == dish_id
        )
        orders_result = await db.execute(orders_query)
        total_orders = orders_result.scalar() or 0
        
        # Общая выручка от блюда
        revenue_query = select(func.sum(OrderItem.total)).where(
            OrderItem.dish_id == dish_id
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or Decimal('0.00')
        
        return {
            "dish_name": dish.name,
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "current_price": dish.price,
            "is_available": dish.is_available
        }
    
    @staticmethod
    async def check_dish_availability(db: AsyncSession, dish_id: int) -> bool:
        """Проверить доступность блюда"""
        query = select(Dish.is_available).where(Dish.id == dish_id)
        result = await db.execute(query)
        return result.scalar() or False
    
    @staticmethod
    async def update_dish_availability(db: AsyncSession, dish_id: int, is_available: bool) -> bool:
        """Обновить доступность блюда"""
        query = update(Dish).where(Dish.id == dish_id).values(is_available=is_available)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def get_dishes_for_menu(db: AsyncSession) -> dict:
        """Получить блюда для публичного меню (сгруппированные по категориям)"""
        query = select(Dish).options(
            selectinload(Dish.category_obj)
        ).where(
            Dish.is_available == True
        ).order_by(Dish.category_id, Dish.name)
        
        result = await db.execute(query)
        dishes = result.scalars().all()
        
        # Группируем по категориям
        menu = {}
        for dish in dishes:
            category_name = dish.category_obj.name
            if category_name not in menu:
                menu[category_name] = {
                    "category_id": dish.category_id,
                    "category_name": category_name,
                    "dishes": []
                }
            
            menu[category_name]["dishes"].append({
                "id": dish.id,
                "name": dish.name,
                "description": dish.description,
                "price": float(dish.price),
                "image_url": dish.image_url,
                "cooking_time": dish.cooking_time,
                "weight": dish.weight,
                "calories": dish.calories,
                "ingredients": dish.ingredients
            })
        
        return menu
    
    @staticmethod
    async def validate_dish_data(dish_data: dict, db: AsyncSession) -> bool:
        """Валидация данных блюда"""
        # Проверяем существование категории
        if 'category_id' in dish_data:
            category_query = select(Category).where(Category.id == dish_data['category_id'])
            category_result = await db.execute(category_query)
            category = category_result.scalar_one_or_none()
            
            if not category or not category.is_active:
                raise ValueError("Категория не найдена или неактивна")
        
        # Проверяем уникальность кода (если указан)
        if 'code' in dish_data and dish_data['code']:
            code_query = select(Dish).where(Dish.code == dish_data['code'])
            code_result = await db.execute(code_query)
            existing_dish = code_result.scalar_one_or_none()
            
            if existing_dish:
                raise ValueError(f"Блюдо с кодом '{dish_data['code']}' уже существует")
        
        return True
