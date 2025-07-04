"""
QRes OS 4 - FastAPI Dependencies
Зависимости для инъекции в роутеры
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .services.auth import AuthService
from .models import User, UserRole
from .schemas import TokenData


# Security scheme
security = HTTPBearer()


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> User:
    """
    Получение текущего аутентифицированного пользователя
    """
    token = credentials.credentials
    token_data = AuthService.verify_token(token)
    
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Получение текущего активного пользователя
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неактивный пользователь"
        )
    return current_user


# Зависимости для проверки ролей
class RoleChecker:
    """Проверка ролей пользователя"""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения этой операции"
            )
        return current_user


# Готовые зависимости для разных ролей
require_admin = RoleChecker([UserRole.ADMIN])
require_waiter = RoleChecker([UserRole.WAITER, UserRole.ADMIN])
require_kitchen = RoleChecker([UserRole.KITCHEN, UserRole.ADMIN])


# Типы для аннотаций
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
WaiterUser = Annotated[User, Depends(require_waiter)]
KitchenUser = Annotated[User, Depends(require_kitchen)]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
