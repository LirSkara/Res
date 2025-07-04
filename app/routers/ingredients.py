"""
QRes OS 4 - Ingredients Router
Роутер для управления ингредиентами
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..deps import DatabaseSession, AdminUser, CurrentUser
from ..models import Ingredient
from ..schemas import (
    Ingredient as IngredientSchema, IngredientCreate, IngredientUpdate,
    IngredientList, APIResponse
)


router = APIRouter()


@router.get("/", response_model=IngredientList)
async def get_ingredients(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    is_allergen: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=100)
):
    """
    Получить список ингредиентов с фильтрацией и поиском
    """
    query = select(Ingredient)
    
    # Фильтры
    if is_allergen is not None:
        query = query.where(Ingredient.is_allergen == is_allergen)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Ingredient.name.ilike(search_term) | 
            Ingredient.description.ilike(search_term)
        )
    
    # Сортировка по названию
    query = query.order_by(Ingredient.name)
    
    # Получение общего количества
    count_query = select(func.count(Ingredient.id))
    if is_allergen is not None:
        count_query = count_query.where(Ingredient.is_allergen == is_allergen)
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            Ingredient.name.ilike(search_term) | 
            Ingredient.description.ilike(search_term)
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    ingredients = result.scalars().all()
    
    return IngredientList(ingredients=ingredients, total=total)


@router.post("/", response_model=IngredientSchema)
async def create_ingredient(
    ingredient_data: IngredientCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новый ингредиент (только для администраторов)
    """
    # Проверяем уникальность названия
    existing_query = select(Ingredient).where(Ingredient.name == ingredient_data.name)
    existing_result = await db.execute(existing_query)
    existing_ingredient = existing_result.scalar_one_or_none()
    
    if existing_ingredient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ингредиент с названием '{ingredient_data.name}' уже существует"
        )
    
    # Создаем ингредиент
    new_ingredient = Ingredient(
        name=ingredient_data.name,
        description=ingredient_data.description,
        is_allergen=ingredient_data.is_allergen
    )
    
    db.add(new_ingredient)
    await db.commit()
    await db.refresh(new_ingredient)
    
    return new_ingredient


@router.get("/{ingredient_id}", response_model=IngredientSchema)
async def get_ingredient(
    ingredient_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию об ингредиенте по ID
    """
    query = select(Ingredient).where(Ingredient.id == ingredient_id)
    result = await db.execute(query)
    ingredient = result.scalar_one_or_none()
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ингредиент не найден"
        )
    
    return ingredient


@router.patch("/{ingredient_id}", response_model=IngredientSchema)
async def update_ingredient(
    ingredient_id: int,
    ingredient_data: IngredientUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию об ингредиенте (только для администраторов)
    """
    query = select(Ingredient).where(Ingredient.id == ingredient_id)
    result = await db.execute(query)
    ingredient = result.scalar_one_or_none()
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ингредиент не найден"
        )
    
    # Проверяем уникальность названия (если изменяется)
    if ingredient_data.name and ingredient_data.name != ingredient.name:
        existing_query = select(Ingredient).where(Ingredient.name == ingredient_data.name)
        existing_result = await db.execute(existing_query)
        existing_ingredient = existing_result.scalar_one_or_none()
        
        if existing_ingredient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ингредиент с названием '{ingredient_data.name}' уже существует"
            )
    
    # Обновляем поля
    update_data = ingredient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ingredient, field, value)
    
    await db.commit()
    await db.refresh(ingredient)
    
    return ingredient


@router.get("/allergens/list")
async def get_allergens(
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить список всех аллергенов
    """
    query = select(Ingredient).where(Ingredient.is_allergen == True).order_by(Ingredient.name)
    result = await db.execute(query)
    allergens = result.scalars().all()
    
    return {
        "allergens": allergens,
        "total": len(allergens)
    }


@router.delete("/{ingredient_id}", response_model=APIResponse)
async def delete_ingredient(
    ingredient_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить ингредиент (только для администраторов)
    """
    query = select(Ingredient).where(Ingredient.id == ingredient_id)
    result = await db.execute(query)
    ingredient = result.scalar_one_or_none()
    
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ингредиент не найден"
        )
    
    # В реальном приложении следует проверить, используется ли ингредиент в блюдах
    # Пока просто удаляем
    await db.delete(ingredient)
    await db.commit()
    
    return APIResponse(
        message=f"Ингредиент '{ingredient.name}' удален"
    )
