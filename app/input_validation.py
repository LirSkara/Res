"""
QRes OS 4 - Input Validation and Sanitization
Валидация и санитизация входных данных для предотвращения инъекций
"""
import re
import html
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from pydantic import BaseModel, validator


class InputSanitizer:
    """Класс для санитизации входных данных"""
    
    # Паттерны для валидации
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\bUNION\s+(ALL\s+)?SELECT)",
        r"(\bINTO\s+(OUT|DUMP)FILE)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
    ]
    
    # Паттерны для проверки имени файла
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Санитизация строки"""
        if not isinstance(value, str):
            return str(value)
        
        # Ограничиваем длину
        if len(value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"Строка превышает максимальную длину {max_length} символов"
            )
        
        # Экранируем HTML
        value = html.escape(value)
        
        # Удаляем null bytes
        value = value.replace('\x00', '')
        
        # Удаляем управляющие символы
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        return value.strip()
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """Проверка на SQL инъекции"""
        value_lower = value.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_xss(cls, value: str) -> bool:
        """Проверка на XSS"""
        value_lower = value.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_filename(cls, filename: str) -> str:
        """Валидация имени файла"""
        if not filename:
            raise HTTPException(status_code=400, detail="Имя файла не может быть пустым")
        
        # Проверяем на опасные символы
        if not cls.FILENAME_PATTERN.match(filename):
            raise HTTPException(
                status_code=400,
                detail="Имя файла содержит недопустимые символы"
            )
        
        # Проверяем на попытки выхода из директории
        if '..' in filename or filename.startswith('/'):
            raise HTTPException(
                status_code=400,
                detail="Недопустимое имя файла"
            )
        
        return filename
    
    @classmethod
    def sanitize_dict(cls, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """Рекурсивная санитизация словаря"""
        if max_depth <= 0:
            raise HTTPException(status_code=400, detail="Слишком глубокая вложенность данных")
        
        sanitized = {}
        for key, value in data.items():
            # Санитизируем ключ
            safe_key = cls.sanitize_string(str(key), max_length=100)
            
            if isinstance(value, str):
                # Проверяем на инъекции
                if cls.check_sql_injection(value):
                    raise HTTPException(status_code=400, detail="Обнаружена попытка SQL инъекции")
                if cls.check_xss(value):
                    raise HTTPException(status_code=400, detail="Обнаружена попытка XSS атаки")
                
                sanitized[safe_key] = cls.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = cls.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = [
                    cls.sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value[:100]  # Ограничиваем количество элементов
                ]
            else:
                sanitized[safe_key] = value
        
        return sanitized


class SecurityValidatorMixin:
    """Миксин для добавления валидации безопасности в Pydantic модели"""
    
    @classmethod
    def __init_subclass__(cls, **kwargs):
        """Автоматически добавляем валидацию безопасности ко всем строковым полям"""
        super().__init_subclass__(**kwargs)
        
        # Для Pydantic V2 мы будем добавлять валидацию в конкретных схемах
        # а не через миксин, чтобы избежать конфликтов


# Декоратор для санитизации запросов
def sanitize_request_data(func):
    """Декоратор для автоматической санитизации данных запроса"""
    async def wrapper(*args, **kwargs):
        # Санитизируем все строковые параметры
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                if InputSanitizer.check_sql_injection(value):
                    raise HTTPException(status_code=400, detail="Обнаружена попытка SQL инъекции")
                if InputSanitizer.check_xss(value):
                    raise HTTPException(status_code=400, detail="Обнаружена попытка XSS атаки")
                sanitized_kwargs[key] = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized_kwargs[key] = InputSanitizer.sanitize_dict(value)
            else:
                sanitized_kwargs[key] = value
        
        return await func(*args, **sanitized_kwargs)
    
    return wrapper
