"""
QRes OS 4 - Dishes Router
Роутер для управления блюдами
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from decimal import Decimal

from ..deps import DatabaseSession, AdminUser, WaiterUser, CurrentUser
from ..models import Dish, Category, DishVariation
from ..schemas import (
    Dish as DishSchema, DishCreate, DishUpdate, DishWithCategory,
    DishAvailabilityUpdate, DishList, MenuResponse, APIResponse,
    DishVariation as DishVariationSchema, DishVariationCreate, DishVariationUpdate,
    DishVariationWithDish, DishVariationList, DishVariationAvailabilityUpdate,
    DishVariationDefaultUpdate
)


router = APIRouter()


@router.get("/", response_model=DishList)
async def get_dishes(
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category_id: Optional[int] = Query(None),
    is_available: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=100)
):
    """
    Получить список блюд с фильтрацией и поиском
    """
    query = select(Dish).options(selectinload(Dish.category_obj))
    
    # Фильтры
    if category_id is not None:
        query = query.where(Dish.category_id == category_id)
    if is_available is not None:
        query = query.where(Dish.is_available == is_available)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Dish.name.ilike(search_term) | 
            Dish.description.ilike(search_term) |
            Dish.ingredients.ilike(search_term)
        )
    
    # Сортировка по названию
    query = query.order_by(Dish.name)
    
    # Получение общего количества
    count_query = select(func.count(Dish.id))
    if category_id is not None:
        count_query = count_query.where(Dish.category_id == category_id)
    if is_available is not None:
        count_query = count_query.where(Dish.is_available == is_available)
    if search:
        search_term = f"%{search}%"
        count_query = count_query.where(
            Dish.name.ilike(search_term) | 
            Dish.description.ilike(search_term) |
            Dish.ingredients.ilike(search_term)
        )
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    dishes = result.scalars().all()
    
    return DishList(dishes=dishes, total=total)


@router.get("/menu", response_model=MenuResponse)
async def get_menu(
    db: DatabaseSession
):
    """
    Получить меню для клиентов (публичный эндпоинт)
    Группировка блюд по категориям
    """
    # Получаем активные категории с активными блюдами
    categories_query = select(Category).where(Category.is_active == True).order_by(Category.sort_order, Category.name)
    categories_result = await db.execute(categories_query)
    categories = categories_result.scalars().all()
    
    menu_categories = []
    
    for category in categories:
        # Получаем доступные блюда в категории
        dishes_query = select(Dish).where(
            Dish.category_id == category.id,
            Dish.is_available == True
        ).order_by(Dish.name)
        dishes_result = await db.execute(dishes_query)
        dishes = dishes_result.scalars().all()
        
        if dishes:  # Добавляем категорию только если есть доступные блюда
            menu_categories.append({
                "category": {
                    "id": category.id,
                    "name": category.name,
                    "description": category.description,
                    "image_url": category.image_url,
                    "sort_order": category.sort_order
                },
                "dishes": [
                    {
                        "id": dish.id,
                        "name": dish.name,
                        "description": dish.description,
                        "main_image_url": dish.main_image_url,
                        "cooking_time": dish.cooking_time,
                        "weight": dish.weight,
                        "calories": dish.calories,
                        "ingredients": dish.ingredients,
                        "sort_order": dish.sort_order,
                        "is_popular": dish.is_popular
                    }
                    for dish in dishes
                ]
            })
    
    return MenuResponse(categories=menu_categories)


@router.post("/", response_model=DishSchema)
async def create_dish(
    dish_data: DishCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новое блюдо (только для администраторов)
    """
    # Проверяем существование категории
    category_query = select(Category).where(Category.id == dish_data.category_id)
    category_result = await db.execute(category_query)
    category = category_result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Указанная категория не найдена"
        )
    
    # Проверяем уникальность названия в категории
    existing_query = select(Dish).where(
        Dish.name == dish_data.name,
        Dish.category_id == dish_data.category_id
    )
    existing_result = await db.execute(existing_query)
    existing_dish = existing_result.scalar_one_or_none()
    
    if existing_dish:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Блюдо с названием '{dish_data.name}' уже существует в этой категории"
        )
    
    # Проверяем уникальность кода (если указан)
    if dish_data.code:
        code_query = select(Dish).where(Dish.code == dish_data.code)
        code_result = await db.execute(code_query)
        code_dish = code_result.scalar_one_or_none()
        
        if code_dish:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Блюдо с кодом '{dish_data.code}' уже существует"
            )
    
    # Создаем блюдо
    new_dish = Dish(
        name=dish_data.name,
        description=dish_data.description,
        category_id=dish_data.category_id,
        code=dish_data.code,
        main_image_url=dish_data.main_image_url,
        cooking_time=dish_data.cooking_time,
        weight=dish_data.weight,
        calories=dish_data.calories,
        ingredients=dish_data.ingredients,
        is_available=dish_data.is_available,
        sort_order=dish_data.sort_order,
        is_popular=dish_data.is_popular
    )
    
    db.add(new_dish)
    await db.commit()
    await db.refresh(new_dish)
    
    return new_dish


@router.get("/{dish_id}", response_model=DishWithCategory)
async def get_dish(
    dish_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить информацию о блюде по ID
    """
    query = select(Dish).options(selectinload(Dish.category_obj)).where(Dish.id == dish_id)
    result = await db.execute(query)
    dish = result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    # Преобразуем в схему с информацией о категории
    dish_dict = {
        "id": dish.id,
        "name": dish.name,
        "description": dish.description,
        "category_id": dish.category_id,
        "code": dish.code,
        "main_image_url": dish.main_image_url,
        "cooking_time": dish.cooking_time,
        "weight": dish.weight,
        "calories": dish.calories,
        "ingredients": dish.ingredients,
        "is_available": dish.is_available,
        "sort_order": dish.sort_order,
        "is_popular": dish.is_popular,
        "created_at": dish.created_at,
        "updated_at": dish.updated_at,
        "category_name": dish.category_obj.name,
        "category_sort_order": dish.category_obj.sort_order
    }
    
    return DishWithCategory(**dish_dict)


@router.patch("/{dish_id}", response_model=DishSchema)
async def update_dish(
    dish_id: int,
    dish_data: DishUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить информацию о блюде (только для администраторов)
    """
    query = select(Dish).where(Dish.id == dish_id)
    result = await db.execute(query)
    dish = result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    # Проверяем существование категории (если изменяется)
    if dish_data.category_id and dish_data.category_id != dish.category_id:
        category_query = select(Category).where(Category.id == dish_data.category_id)
        category_result = await db.execute(category_query)
        category = category_result.scalar_one_or_none()
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанная категория не найдена"
            )
    
    # Проверяем уникальность названия в категории (если изменяется)
    check_category_id = dish_data.category_id if dish_data.category_id else dish.category_id
    if dish_data.name and (dish_data.name != dish.name or dish_data.category_id):
        existing_query = select(Dish).where(
            Dish.name == dish_data.name,
            Dish.category_id == check_category_id,
            Dish.id != dish_id
        )
        existing_result = await db.execute(existing_query)
        existing_dish = existing_result.scalar_one_or_none()
        
        if existing_dish:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Блюдо с названием '{dish_data.name}' уже существует в этой категории"
            )
    
    # Проверяем уникальность кода (если изменяется)
    if dish_data.code and dish_data.code != dish.code:
        code_query = select(Dish).where(Dish.code == dish_data.code, Dish.id != dish_id)
        code_result = await db.execute(code_query)
        code_dish = code_result.scalar_one_or_none()
        
        if code_dish:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Блюдо с кодом '{dish_data.code}' уже существует"
            )
    
    # Обновляем поля
    update_data = dish_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dish, field, value)
    
    await db.commit()
    await db.refresh(dish)
    
    return dish


@router.patch("/{dish_id}/availability", response_model=APIResponse)
async def update_dish_availability(
    dish_id: int,
    availability_data: DishAvailabilityUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Быстрое изменение доступности блюда (для кухни и администраторов)
    """
    query = select(Dish).where(Dish.id == dish_id)
    result = await db.execute(query)
    dish = result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    dish.is_available = availability_data.is_available
    await db.commit()
    
    status_text = "доступно" if availability_data.is_available else "недоступно"
    return APIResponse(
        message=f"Блюдо '{dish.name}' теперь {status_text}"
    )


@router.delete("/{dish_id}", response_model=APIResponse)
async def delete_dish(
    dish_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить блюдо (только для администраторов)
    """
    query = select(Dish).where(Dish.id == dish_id)
    result = await db.execute(query)
    dish = result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    # Проверяем, есть ли активные заказы с этим блюдом
    # Это можно реализовать позже при создании OrderItem
    
    # Деактивируем вместо удаления для сохранения истории
    dish.is_available = False
    await db.commit()
    
    return APIResponse(
        message=f"Блюдо '{dish.name}' деактивировано"
    )


# ========== DISH VARIATIONS ENDPOINTS ==========

@router.get("/{dish_id}/variations/", response_model=DishVariationList)
async def get_dish_variations(
    dish_id: int,
    db: DatabaseSession,
    current_user: CurrentUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    available_only: bool = Query(False)
):
    """
    Получить список вариаций блюда
    """
    # Проверяем существование блюда
    dish_query = select(Dish).where(Dish.id == dish_id)
    dish_result = await db.execute(dish_query)
    dish = dish_result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    # Формируем запрос вариаций
    query = select(DishVariation).where(DishVariation.dish_id == dish_id)
    
    if available_only:
        query = query.where(DishVariation.is_available == True)
    
    # Сортировка: сначала по умолчанию, потом по sort_order
    query = query.order_by(DishVariation.is_default.desc(), DishVariation.sort_order, DishVariation.name)
    
    # Подсчет общего количества
    count_query = select(func.count(DishVariation.id)).where(DishVariation.dish_id == dish_id)
    if available_only:
        count_query = count_query.where(DishVariation.is_available == True)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    variations = result.scalars().all()
    
    return DishVariationList(variations=variations, total=total)


@router.post("/{dish_id}/variations/", response_model=DishVariationSchema, status_code=status.HTTP_201_CREATED)
async def create_dish_variation(
    dish_id: int,
    variation_data: DishVariationCreate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Создать новую вариацию блюда (только для администраторов)
    """
    # Проверяем существование блюда
    dish_query = select(Dish).where(Dish.id == dish_id)
    dish_result = await db.execute(dish_query)
    dish = dish_result.scalar_one_or_none()
    
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Блюдо не найдено"
        )
    
    # Проверяем уникальность SKU (если указан)
    if variation_data.sku:
        sku_query = select(DishVariation).where(DishVariation.sku == variation_data.sku)
        sku_result = await db.execute(sku_query)
        existing_sku = sku_result.scalar_one_or_none()
        
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Вариация с SKU '{variation_data.sku}' уже существует"
            )
    
    # Если это первая вариация или явно указано is_default=True
    if variation_data.is_default:
        # Убираем флаг по умолчанию у других вариаций этого блюда
        await db.execute(
            update(DishVariation)
            .where(DishVariation.dish_id == dish_id)
            .values(is_default=False)
        )
    else:
        # Проверяем, есть ли уже вариация по умолчанию
        default_query = select(DishVariation).where(
            DishVariation.dish_id == dish_id,
            DishVariation.is_default == True
        )
        default_result = await db.execute(default_query)
        has_default = default_result.scalar_one_or_none()
        
        # Если нет вариации по умолчанию, делаем эту по умолчанию
        if not has_default:
            variation_data.is_default = True
    
    # Создаем вариацию
    new_variation = DishVariation(
        dish_id=dish_id,
        **variation_data.model_dump()
    )
    
    db.add(new_variation)
    await db.commit()
    await db.refresh(new_variation)
    
    return new_variation


@router.get("/{dish_id}/variations/{variation_id}", response_model=DishVariationSchema)
async def get_dish_variation(
    dish_id: int,
    variation_id: int,
    db: DatabaseSession,
    current_user: CurrentUser
):
    """
    Получить вариацию блюда по ID
    """
    variation_query = select(DishVariation).where(
        DishVariation.id == variation_id,
        DishVariation.dish_id == dish_id
    )
    
    variation_result = await db.execute(variation_query)
    variation = variation_result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вариация блюда не найдена"
        )
    
    return variation


@router.patch("/{dish_id}/variations/{variation_id}", response_model=DishVariationSchema)
async def update_dish_variation(
    dish_id: int,
    variation_id: int,
    variation_data: DishVariationUpdate,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Обновить вариацию блюда (только для администраторов)
    """
    # Загружаем вариацию
    variation_query = select(DishVariation).where(
        DishVariation.id == variation_id,
        DishVariation.dish_id == dish_id
    )
    
    variation_result = await db.execute(variation_query)
    variation = variation_result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вариация блюда не найдена"
        )
    
    # Проверяем уникальность SKU (если обновляется)
    if variation_data.sku and variation_data.sku != variation.sku:
        sku_query = select(DishVariation).where(DishVariation.sku == variation_data.sku)
        sku_result = await db.execute(sku_query)
        existing_sku = sku_result.scalar_one_or_none()
        
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Вариация с SKU '{variation_data.sku}' уже существует"
            )
    
    # Обрабатываем флаг по умолчанию
    if variation_data.is_default is True and not variation.is_default:
        # Убираем флаг по умолчанию у других вариаций
        await db.execute(
            update(DishVariation)
            .where(
                DishVariation.dish_id == dish_id,
                DishVariation.id != variation_id
            )
            .values(is_default=False)
        )
    
    # Обновляем поля
    update_data = variation_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variation, field, value)
    
    await db.commit()
    await db.refresh(variation)
    
    return variation


@router.patch("/{dish_id}/variations/{variation_id}/availability", response_model=APIResponse)
async def update_variation_availability(
    dish_id: int,
    variation_id: int,
    availability_data: DishVariationAvailabilityUpdate,
    db: DatabaseSession,
    waiter_user: WaiterUser
):
    """
    Обновить доступность вариации (для официантов и администраторов)
    """
    variation_query = select(DishVariation).where(
        DishVariation.id == variation_id,
        DishVariation.dish_id == dish_id
    )
    
    variation_result = await db.execute(variation_query)
    variation = variation_result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вариация блюда не найдена"
        )
    
    variation.is_available = availability_data.is_available
    await db.commit()
    
    status_text = "доступна" if availability_data.is_available else "недоступна"
    return APIResponse(
        message=f"Вариация '{variation.name}' теперь {status_text}"
    )


@router.delete("/{dish_id}/variations/{variation_id}", response_model=APIResponse)
async def delete_dish_variation(
    dish_id: int,
    variation_id: int,
    db: DatabaseSession,
    admin_user: AdminUser
):
    """
    Удалить вариацию блюда (только для администраторов)
    """
    # Проверяем что вариация существует
    variation_query = select(DishVariation).where(
        DishVariation.id == variation_id,
        DishVariation.dish_id == dish_id
    )
    
    variation_result = await db.execute(variation_query)
    variation = variation_result.scalar_one_or_none()
    
    if not variation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вариация блюда не найдена"
        )
    
    # Проверяем, что это не единственная вариация
    count_query = select(func.count(DishVariation.id)).where(DishVariation.dish_id == dish_id)
    count_result = await db.execute(count_query)
    total_variations = count_result.scalar()
    
    if total_variations <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить единственную вариацию блюда"
        )
    
    # Если удаляем вариацию по умолчанию, назначаем другую
    if variation.is_default:
        other_variation_query = select(DishVariation).where(
            DishVariation.dish_id == dish_id,
            DishVariation.id != variation_id
        ).limit(1)
        
        other_variation_result = await db.execute(other_variation_query)
        other_variation = other_variation_result.scalar_one_or_none()
        
        if other_variation:
            other_variation.is_default = True
    
    # Удаляем вариацию
    await db.delete(variation)
    await db.commit()
    
    return APIResponse(
        message="Вариация блюда удалена"
    )
