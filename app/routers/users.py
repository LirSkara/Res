"""
QRes OS 4 - Users Router
Роутер для управления пользователями (только для администраторов)
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from ..models import User, UserRole
from ..schemas import (
    UserCreate, UserUpdate, UserChangePassword, User as UserSchema, 
    UserList, APIResponse
)
from ..services.auth import AuthService
from ..deps import AdminUser, DatabaseSession


router = APIRouter()


@router.get("/", response_model=UserList)
async def get_users(
    db: DatabaseSession,
    current_user: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Получение списка пользователей с фильтрацией
    Только для администраторов
    """
    query = select(User)
    
    # Фильтры
    conditions = []
    
    if role:
        conditions.append(User.role == role)
    
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        conditions.append(
            User.username.ilike(search_term) | 
            User.full_name.ilike(search_term)
        )
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Подсчет общего количества
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Получение пользователей с пагинацией
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserList(
        users=[UserSchema.model_validate(user) for user in users],
        total=total
    )


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Создание нового пользователя
    Только для администраторов
    """
    # Проверка уникальности логина
    existing_user = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует"
        )
    
    # Проверка уникальности PIN-кода (если указан)
    if user_data.pin_code:
        existing_pin = await db.execute(
            select(User).where(User.pin_code == user_data.pin_code)
        )
        if existing_pin.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким PIN-кодом уже существует"
            )
    
    # Создание пользователя
    user = User(
        username=user_data.username,
        password_hash=AuthService.hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        passport=user_data.passport,
        avatar_url=user_data.avatar_url,
        pin_code=user_data.pin_code,
        is_active=user_data.is_active,
        shift_active=user_data.shift_active,
        created_by_id=current_user.id
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserSchema.model_validate(user)


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: int,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Получение пользователя по ID
    Только для администраторов
    """
    user = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return UserSchema.model_validate(user)


@router.patch("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Обновление данных пользователя
    Только для администраторов
    """
    user = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка уникальности PIN-кода (если изменяется)
    if user_update.pin_code and user_update.pin_code != user.pin_code:
        existing_pin = await db.execute(
            select(User).where(
                User.pin_code == user_update.pin_code,
                User.id != user_id
            )
        )
        if existing_pin.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким PIN-кодом уже существует"
            )
    
    # Обновление полей
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return UserSchema.model_validate(user)


@router.patch("/{user_id}/password", response_model=APIResponse)
async def change_user_password(
    user_id: int,
    password_data: UserChangePassword,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Смена пароля пользователя
    Только для администраторов
    """
    user = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверка текущего пароля
    if not AuthService.verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Установка нового пароля
    user.password_hash = AuthService.hash_password(password_data.new_password)
    await db.commit()
    
    return APIResponse(
        success=True,
        message="Пароль успешно изменен"
    )


@router.delete("/{user_id}", response_model=APIResponse)
async def delete_user(
    user_id: int,
    db: DatabaseSession,
    current_user: AdminUser
):
    """
    Удаление (деактивация) пользователя
    Только для администраторов
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    user = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Деактивация вместо удаления
    user.is_active = False
    user.shift_active = False
    await db.commit()
    
    return APIResponse(
        success=True,
        message=f"Пользователь {user.username} деактивирован"
    )
