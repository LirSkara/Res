"""
QRes OS 4 - Categories Router
Роутер для управления категориями блюд
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..deps import DatabaseSession, AdminUser, CurrentUser
from ..models import Category, Dish
from ..schemas import (
    Category as CategorySchema, CategoryCreate, CategoryUpdate,
    CategoryWithDishes, CategoryList, APIResponse
)


router = APIRouter()


@router.get("/", response_model=CategoryList)
async def get_categories(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None)
):
    """
    Получить список категорий с фильтрацией
    """
    query = select(Category)
    
    # Фильтры
    if is_active is not None:
        query = query.where(Category.is_active == is_active)
    
    # Сортировка по порядку отображения, затем по названию
    query = query.order_by(Category.sort_order, Category.name)
    
    # Получение общего количества
    count_query = select(func.count(Category.id))
    if is_active is not None:
        count_query = count_query.where(Category.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return CategoryList(categories=categories, total=total)


@router.post("/", response_model=CategorySchema)
async def create_category(
    category_data: CategoryCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новую категорию (только для администраторов)
    """
    # Проверяем уникальность названия
    existing_query = select(Category).where(Category.name == category_data.name)
    existing_result = await db.execute(existing_query)
    existing_category = existing_result.scalar_one_or_none()
    
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Категория с названием '{category_data.name}' уже существует"
        )
    
    # Создаем категорию
    new_category = Category(
        name=category_data.name,
        description=category_data.description,
        image_url=category_data.image_url,
        sort_order=category_data.sort_order,
        is_active=category_data.is_active
    )
    
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    return new_category


@router.get("/{category_id}", response_model=CategoryWithDishes)
async def get_category(
    category_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о категории по ID
    """
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Подсчитываем количество блюд в категории
    dishes_count_query = select(func.count(Dish.id)).where(Dish.category_id == category_id)
    dishes_count_result = await db.execute(dishes_count_query)
    dishes_count = dishes_count_result.scalar()
    
    # Подсчитываем количество активных блюд
    active_dishes_count_query = select(func.count(Dish.id)).where(
        Dish.category_id == category_id,
        Dish.is_available == True
    )
    active_dishes_count_result = await db.execute(active_dishes_count_query)
    active_dishes_count = active_dishes_count_result.scalar()
    
    # Преобразуем в схему с количеством блюд
    category_dict = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "image_url": category.image_url,
        "sort_order": category.sort_order,
        "is_active": category.is_active,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
        "dishes_count": dishes_count,
        "active_dishes_count": active_dishes_count
    }
    
    return CategoryWithDishes(**category_dict)


@router.patch("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию о категории (только для администраторов)
    """
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем уникальность названия (если изменяется)
    if category_data.name and category_data.name != category.name:
        existing_query = select(Category).where(Category.name == category_data.name)
        existing_result = await db.execute(existing_query)
        existing_category = existing_result.scalar_one_or_none()
        
        if existing_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Категория с названием '{category_data.name}' уже существует"
            )
    
    # Обновляем поля
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    
    return category


@router.get("/{category_id}/dishes")
async def get_category_dishes(
    category_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_available: Optional[bool] = Query(None)
):
    """
    Получить список блюд в категории
    """
    # Проверяем существование категории
    category_query = select(Category).where(Category.id == category_id)
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Получаем блюда
    dishes_query = select(Dish).where(Dish.category_id == category_id)
    
    if is_available is not None:
        dishes_query = dishes_query.where(Dish.is_available == is_available)
    
    dishes_query = dishes_query.order_by(Dish.name)
    dishes_query = dishes_query.offset(skip).limit(limit)
    dishes_result = await db.execute(dishes_query)
    dishes = dishes_result.scalars().all()
    
    # Получаем общее количество
    count_query = select(func.count(Dish.id)).where(Dish.category_id == category_id)
    if is_available is not None:
        count_query = count_query.where(Dish.is_available == is_available)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return {
        "dishes": dishes,
        "total": total,
        "category": category
    }


@router.delete("/{category_id}", response_model=APIResponse)
async def delete_category(
    category_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить или деактивировать категорию (только для администраторов)
    """
    query = select(Category).where(Category.id == category_id)
    result = await db.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Категория не найдена"
        )
    
    # Проверяем, есть ли блюда в категории
    dishes_query = select(func.count(Dish.id)).where(Dish.category_id == category_id)
    dishes_result = await db.execute(dishes_query)
    dishes_count = dishes_result.scalar()
    
    if dishes_count > 0:
        # Деактивируем вместо удаления
        category.is_active = False
        await db.commit()
        
        return APIResponse(
            message=f"Категория '{category.name}' деактивирована (содержит {dishes_count} блюд)"
        )
    else:
        # Полное удаление, если нет блюд
        await db.delete(category)
        await db.commit()
        
        return APIResponse(
            message=f"Категория '{category.name}' удалена"
        )
