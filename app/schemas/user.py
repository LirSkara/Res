"""
QRes OS 4 - User Schemas
Pydantic схемы для пользователей
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import datetime
from ..models.user import UserRole
import re


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
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        # Импортируем здесь, чтобы избежать циклических импортов
        from ..input_validation import InputSanitizer
        
        # Санитизируем и проверяем на атаки
        if InputSanitizer.check_sql_injection(v):
            raise ValueError("Обнаружена попытка SQL инъекции")
        if InputSanitizer.check_xss(v):
            raise ValueError("Обнаружена попытка XSS атаки")
        
        v = InputSanitizer.sanitize_string(v)
        
        # Проверяем на допустимые символы (буквы, цифры, подчеркивание, дефис)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username может содержать только буквы, цифры, _ и -')
        
        return v
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        from ..input_validation import InputSanitizer
        
        if InputSanitizer.check_sql_injection(v):
            raise ValueError("Обнаружена попытка SQL инъекции")
        if InputSanitizer.check_xss(v):
            raise ValueError("Обнаружена попытка XSS атаки")
        
        return InputSanitizer.sanitize_string(v)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            from ..input_validation import InputSanitizer
            
            if InputSanitizer.check_sql_injection(v):
                raise ValueError("Обнаружена попытка SQL инъекции")
            
            # Удаляем все символы кроме цифр и +
            phone_clean = re.sub(r'[^\d+]', '', v)
            # Более гибкая валидация телефона - разрешаем номера, начинающиеся с 0
            if not re.match(r'^\+?[0-9]\d{7,14}$', phone_clean):
                raise ValueError('Неверный формат номера телефона')
        return v


class UserCreate(UserBase):
    """Схема создания пользователя"""
    password: str = Field(..., min_length=8, max_length=128)  # Увеличили минимальную длину
    created_by_id: Optional[int] = None
    
    @field_validator('username')
    @classmethod
    def validate_username_create(cls, v):
        # Дополнительная проверка для создания - здесь мы можем проверить зарезервированные имена
        from ..input_validation import InputSanitizer
        
        # Базовая валидация безопасности
        if InputSanitizer.check_sql_injection(v):
            raise ValueError("Обнаружена попытка SQL инъекции")
        if InputSanitizer.check_xss(v):
            raise ValueError("Обнаружена попытка XSS атаки")
        
        v = InputSanitizer.sanitize_string(v)
        
        # Проверяем на допустимые символы
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username может содержать только буквы, цифры, _ и -')
        
        # Проверяем на зарезервированные имена только при создании
        reserved = ['root', 'administrator', 'system', 'guest', 'user', 'test', 'null', 'undefined']
        if v.lower() in reserved:
            raise ValueError('Это имя пользователя зарезервировано')
        
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        from ..input_validation import InputSanitizer
        
        # Проверяем на атаки
        if InputSanitizer.check_sql_injection(v):
            raise ValueError("Обнаружена попытка SQL инъекции")
        
        # Проверяем сложность пароля
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        
        if not re.search(r'\d', v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Пароль должен содержать хотя бы один специальный символ')
        
        # Проверяем на распространенные пароли
        common_passwords = [
            'password', '123456', 'qwerty', 'admin', 'letmein',
            'welcome', 'monkey', '1234567890', 'password123'
        ]
        if v.lower() in common_passwords:
            raise ValueError('Этот пароль слишком распространенный')
        
        return v
    
    @field_validator('pin_code')
    @classmethod
    def validate_pin_code(cls, v):
        if v is not None:
            if not v.isdigit():
                raise ValueError('PIN-код должен содержать только цифры')
            # Проверяем на простые последовательности
            if v in ['1234', '4321', '0000', '1111', '2222', '3333', '4444', '5555', '6666', '7777', '8888', '9999']:
                raise ValueError('PIN-код слишком простой')
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
    
    @field_validator('pin_code')
    @classmethod
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
