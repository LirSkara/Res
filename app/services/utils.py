"""
QRes OS 4 - Utilities
Общие утилиты и вспомогательные функции (согласно ТЗ)
"""
import uuid
import qrcode
from io import BytesIO
import base64
from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
import hashlib


def generate_qr_code(table_id: int, base_url: str = "http://localhost:8000") -> str:
    """Генерация QR-кода для столика"""
    qr_data = f"{base_url}/menu?table={table_id}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Конвертируем в base64 для хранения в БД
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str


def generate_unique_code() -> str:
    """Генерация уникального кода (UUID)"""
    return str(uuid.uuid4())


def format_price(price: Decimal) -> str:
    """Форматирование цены для отображения"""
    return f"{price:.2f} ₽"


def calculate_cooking_time(dish_ids: list, cooking_times: dict) -> Optional[int]:
    """Расчёт времени приготовления заказа"""
    if not dish_ids or not cooking_times:
        return None
    
    max_time = 0
    for dish_id in dish_ids:
        dish_time = cooking_times.get(dish_id, 0)
        if dish_time and dish_time > max_time:
            max_time = dish_time
    
    return max_time if max_time > 0 else None


def validate_phone_number(phone: str) -> bool:
    """Валидация номера телефона"""
    if not phone:
        return True  # Опциональное поле
    
    # Простая валидация для российских номеров
    cleaned = ''.join(filter(str.isdigit, phone))
    
    if len(cleaned) == 11 and cleaned.startswith('7'):
        return True
    elif len(cleaned) == 10 and cleaned.startswith('9'):
        return True
    
    return False


def generate_pin_hash(pin: str) -> str:
    """Генерация хеша для PIN-кода"""
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Проверка PIN-кода"""
    return generate_pin_hash(pin) == pin_hash


def calculate_order_eta(cooking_time: Optional[int]) -> Optional[datetime]:
    """Расчёт примерного времени готовности заказа"""
    if not cooking_time:
        return None
    
    return datetime.utcnow() + timedelta(minutes=cooking_time)


def format_duration(minutes: int) -> str:
    """Форматирование длительности в читаемый вид"""
    if minutes < 60:
        return f"{minutes} мин"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if mins == 0:
        return f"{hours} ч"
    
    return f"{hours} ч {mins} мин"


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    import re
    # Удаляем/заменяем недопустимые символы
    sanitized = re.sub(r'[^\w\s-.]', '', filename)
    # Заменяем пробелы на подчёркивания
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized


def get_file_extension(filename: str) -> str:
    """Получение расширения файла"""
    return filename.split('.')[-1].lower() if '.' in filename else ''


def is_valid_image_extension(extension: str) -> bool:
    """Проверка, является ли расширение допустимым для изображений"""
    valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    return extension.lower() in valid_extensions


class TableStatusManager:
    """Менеджер статусов столиков"""
    
    @staticmethod
    def can_occupy_table(table_status: dict) -> bool:
        """Проверка, можно ли занять столик"""
        return (table_status.get('is_active', False) and 
                not table_status.get('is_occupied', False))
    
    @staticmethod
    def calculate_table_turnover(occupied_time: timedelta) -> str:
        """Расчёт оборачиваемости столика"""
        hours = occupied_time.total_seconds() / 3600
        
        if hours < 1:
            return "Быстрый оборот"
        elif hours < 2:
            return "Средний оборот"
        else:
            return "Медленный оборот"


class OrderStatusManager:
    """Менеджер статусов заказов"""
    
    @staticmethod
    def can_cancel_order(order_status: str) -> bool:
        """Проверка, можно ли отменить заказ"""
        cancelable_statuses = ['pending', 'in_progress']
        return order_status in cancelable_statuses
    
    @staticmethod
    def can_modify_order(order_status: str) -> bool:
        """Проверка, можно ли изменить заказ"""
        modifiable_statuses = ['pending']
        return order_status in modifiable_statuses
    
    @staticmethod
    def get_next_status(current_status: str) -> Optional[str]:
        """Получение следующего логичного статуса"""
        status_flow = {
            'pending': 'in_progress',
            'in_progress': 'ready',
            'ready': 'served'
        }
        return status_flow.get(current_status)


def format_currency(amount: Decimal, currency: str = "₽") -> str:
    """Форматирование суммы с валютой"""
    return f"{amount:.2f} {currency}"


def calculate_tip_suggestions(total: Decimal) -> dict:
    """Расчёт рекомендуемых чаевых"""
    return {
        "5_percent": total * Decimal('0.05'),
        "10_percent": total * Decimal('0.10'),
        "15_percent": total * Decimal('0.15'),
        "20_percent": total * Decimal('0.20')
    }
