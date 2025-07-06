"""
QRes OS 4 - Authentication Service
Сервис аутентификации и авторизации
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from ..models import User, UserRole
from ..schemas import TokenData
from ..config import settings


# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Сервис аутентификации"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, fresh: bool = False) -> str:
        """Создание JWT токена с улучшенной безопасностью"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        # Добавляем дополнительные claims для безопасности
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),  # Время выдачи токена
            "iss": settings.jwt_issuer,  # Издатель токена
            "aud": settings.jwt_audience,  # Аудитория токена
            "fresh": fresh,  # Флаг "свежести" токена для критичных операций
            "jti": secrets.token_hex(16)  # Уникальный ID токена для отзыва
        })
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, require_fresh: bool = False) -> TokenData:
        """Проверка и декодирование JWT токена с улучшенной безопасностью"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        fresh_token_required_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется свежий токен для этой операции",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer
            )
            
            username: str = payload.get("sub")
            user_id: int = payload.get("user_id")
            role: str = payload.get("role")
            issued_at: int = payload.get("iat")
            fresh: bool = payload.get("fresh", False)
            
            if username is None or user_id is None:
                raise credentials_exception
            
            # Проверяем требование "свежести" токена
            if require_fresh and not fresh:
                # Проверяем, не слишком ли старый токен
                if issued_at:
                    token_age_minutes = (datetime.utcnow().timestamp() - issued_at) / 60
                    if token_age_minutes > settings.require_fresh_token_minutes:
                        raise fresh_token_required_exception
                
            token_data = TokenData(
                username=username,
                user_id=user_id,
                role=UserRole(role) if role else None
            )
            return token_data
            
        except JWTError:
            raise credentials_exception
    
    @staticmethod
    async def authenticate_user(
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """Аутентификация пользователя по логину и паролю"""
        query = select(User).where(
            User.username == username,
            User.is_active == True
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user.password_hash):
            return None
        
        # Обновляем время последнего входа
        user.last_login = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def authenticate_user_pin(
        db: AsyncSession, 
        username: str, 
        pin_code: str
    ) -> Optional[User]:
        """Аутентификация пользователя по логину и PIN-коду"""
        if not pin_code or not pin_code.isdigit():
            return None
        
        query = select(User).where(
            User.username == username,
            User.pin_code == pin_code,
            User.is_active == True
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем время последнего входа
            user.last_login = datetime.utcnow()
            await db.commit()
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        query = select(User).where(
            User.id == user_id,
            User.is_active == True
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    def check_role_permission(user_role: UserRole, required_roles: list[UserRole]) -> bool:
        """Проверка прав доступа по роли"""
        return user_role in required_roles
    
    @staticmethod
    def require_admin(user_role: UserRole) -> bool:
        """Проверка прав администратора"""
        return user_role == UserRole.ADMIN
    
    @staticmethod
    def require_waiter_or_admin(user_role: UserRole) -> bool:
        """Проверка прав официанта или администратора"""
        return user_role in [UserRole.WAITER, UserRole.ADMIN]
    
    @staticmethod
    def require_kitchen_or_admin(user_role: UserRole) -> bool:
        """Проверка прав кухни или администратора"""
        return user_role in [UserRole.KITCHEN, UserRole.ADMIN]
