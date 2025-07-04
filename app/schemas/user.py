"""
QRes OS 4 - User Schemas
Pydantic схемы для пользователей
"""
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List
from datetime import datetime
from ..models.user import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole
    phone: Optional[str] = Field(None, max_length=20)
    passport: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=255)
    pin_code: Optional[str] = Field(None, min_length=4, max_length=6)
    is_active: bool = True
    shift_active: bool = False


class UserCreate(UserBase):
    """Схема создания пользователя"""
    password: str = Field(..., min_length=6, max_length=128)
    created_by_id: Optional[int] = None
    
    @validator('pin_code')
    def validate_pin_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError('PIN-код должен содержать только цифры')
        return v


class UserUpdate(BaseModel):
    """Схема обновления пользователя"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRole] = None
    phone: Optional[str] = Field(None, max_length=20)
    passport: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = Field(None, max_length=255)
    pin_code: Optional[str] = Field(None, min_length=4, max_length=6)
    is_active: Optional[bool] = None
    shift_active: Optional[bool] = None
    
    @validator('pin_code')
    def validate_pin_code(cls, v):
        if v is not None and not v.isdigit():
            raise ValueError('PIN-код должен содержать только цифры')
        return v


class UserChangePassword(BaseModel):
    """Схема смены пароля"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class User(UserBase):
    """Полная схема пользователя для ответов"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_by_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserList(BaseModel):
    """Схема списка пользователей"""
    users: List[User]
    total: int


class UserLogin(BaseModel):
    """Схема входа в систему"""
    username: str
    password: str


class UserLoginPIN(BaseModel):
    """Схема входа по PIN-коду"""
    username: str
    pin_code: str


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Данные токена"""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None
