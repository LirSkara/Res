"""
QRes OS 4 - Timezone Utilities
Утилиты для работы с временными зонами
"""
from datetime import datetime, timezone
import pytz
from ..config import settings


def get_moscow_timezone():
    """Получить часовой пояс Москвы"""
    return pytz.timezone(settings.restaurant_timezone)


def get_current_moscow_time() -> datetime:
    """Получить текущее время в московском часовом поясе"""
    moscow_tz = get_moscow_timezone()
    return datetime.now(moscow_tz)


def utc_to_moscow(utc_time: datetime) -> datetime:
    """Конвертировать UTC время в московское"""
    if utc_time.tzinfo is None:
        # Если время без timezone, считаем его UTC
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    
    moscow_tz = get_moscow_timezone()
    return utc_time.astimezone(moscow_tz)


def moscow_to_utc(moscow_time: datetime) -> datetime:
    """Конвертировать московское время в UTC"""
    moscow_tz = get_moscow_timezone()
    
    if moscow_time.tzinfo is None:
        # Если время без timezone, считаем его московским
        moscow_time = moscow_tz.localize(moscow_time)
    
    return moscow_time.astimezone(timezone.utc)


def format_moscow_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматировать время в московском часовом поясе"""
    moscow_time = utc_to_moscow(dt) if dt.tzinfo == timezone.utc else dt
    return moscow_time.strftime(format_str)
