"""
QRes OS 4 - Authentication Router
Роутер для аутентификации и авторизации
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.auth import AuthService
from ..schemas import UserLogin, UserLoginPIN, Token, User as UserSchema, APIResponse
from ..deps import CurrentUser, DatabaseSession
from ..config import settings
from ..security_monitor import security_monitor
from ..security_logger import security_logger


router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin,
    request: Request,
    db: DatabaseSession
):
    """
    Вход в систему по логину и паролю
    """
    client_ip = security_monitor.get_client_ip(request)
    
    user = await AuthService.authenticate_user(
        db, 
        user_credentials.username, 
        user_credentials.password
    )
    
    if not user:
        # Записываем неудачную попытку входа
        security_monitor.record_failed_login(client_ip, user_credentials.username)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Логируем успешный вход
    security_logger.log_successful_login(client_ip, user.username, user.role.value)
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/login/pin", response_model=Token)
async def login_pin(
    user_credentials: UserLoginPIN,
    db: DatabaseSession
):
    """
    Быстрый вход в систему по логину и PIN-коду
    """
    user = await AuthService.authenticate_user_pin(
        db,
        user_credentials.username,
        user_credentials.pin_code
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или PIN-код",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = AuthService.create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: CurrentUser):
    """
    Получение информации о текущем пользователе
    """
    return current_user


@router.post("/logout", response_model=APIResponse)
async def logout(current_user: CurrentUser):
    """
    Выход из системы
    На стороне клиента токен должен быть удален
    """
    return APIResponse(
        success=True,
        message=f"Пользователь {current_user.username} успешно вышел из системы"
    )
