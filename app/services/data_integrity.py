"""
QRes OS 4 - Data Integrity Utilities
Утилиты для проверки и исправления целостности данных
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from ..models import Location, Table, Order
from ..logger import get_logger

logger = get_logger(__name__)


async def check_data_integrity(db: AsyncSession) -> Dict[str, Any]:
    """
    Проверяет целостность данных между локациями и столиками
    
    Returns:
        Dict с результатами проверки
    """
    integrity_report = {
        "timestamp": None,
        "issues_found": False,
        "locations": {
            "total": 0,
            "active": 0,
            "inactive": 0
        },
        "tables": {
            "total": 0,
            "active": 0,
            "inactive": 0,
            "without_location": 0,
            "with_active_orders": 0
        },
        "integrity_issues": [],
        "recommendations": []
    }
    
    # Получаем статистику по локациям
    locations_query = select(Location)
    locations_result = await db.execute(locations_query)
    locations = locations_result.scalars().all()
    
    integrity_report["locations"]["total"] = len(locations)
    integrity_report["locations"]["active"] = sum(1 for loc in locations if loc.is_active)
    integrity_report["locations"]["inactive"] = len(locations) - integrity_report["locations"]["active"]
    
    # Получаем все столики с локациями
    tables_query = select(Table).options(selectinload(Table.location_obj))
    tables_result = await db.execute(tables_query)
    tables = tables_result.scalars().all()
    
    integrity_report["tables"]["total"] = len(tables)
    integrity_report["tables"]["active"] = sum(1 for table in tables if table.is_active)
    integrity_report["tables"]["inactive"] = len(tables) - integrity_report["tables"]["active"]
    integrity_report["tables"]["without_location"] = sum(1 for table in tables if not table.location_id)
    integrity_report["tables"]["with_active_orders"] = sum(1 for table in tables if table.current_order_id)
    
    # Проверяем каждый столик на целостность
    for table in tables:
        issues = []
        
        # Проверка 1: Активный столик в неактивной локации
        if table.is_active and table.location_obj and not table.location_obj.is_active:
            issues.append({
                "type": "active_table_inactive_location",
                "table_id": table.id,
                "table_number": table.number,
                "location_name": table.location_obj.name,
                "description": f"Столик {table.number} активен в неактивной локации '{table.location_obj.name}'"
            })
        
        # Проверка 2: Столик с заказом в неактивной локации
        if table.current_order_id and table.location_obj and not table.location_obj.is_active:
            issues.append({
                "type": "order_in_inactive_location",
                "table_id": table.id,
                "table_number": table.number,
                "order_id": table.current_order_id,
                "location_name": table.location_obj.name,
                "description": f"У столика {table.number} есть заказ в неактивной локации '{table.location_obj.name}'"
            })
        
        # Проверка 3: Активный столик без локации
        if table.is_active and not table.location_obj:
            issues.append({
                "type": "active_table_no_location",
                "table_id": table.id,
                "table_number": table.number,
                "description": f"Активный столик {table.number} не привязан к локации"
            })
        
        # Проверка 4: Занятый но неактивный столик
        if table.is_occupied and not table.is_active:
            issues.append({
                "type": "occupied_inactive_table",
                "table_id": table.id,
                "table_number": table.number,
                "description": f"Столик {table.number} помечен как занятый, но неактивен"
            })
        
        # Проверка 5: Заказ у неактивного столика
        if table.current_order_id and not table.is_active:
            issues.append({
                "type": "order_at_inactive_table",
                "table_id": table.id,
                "table_number": table.number,
                "order_id": table.current_order_id,
                "description": f"У неактивного столика {table.number} есть активный заказ"
            })
        
        integrity_report["integrity_issues"].extend(issues)
    
    # Генерируем рекомендации
    if integrity_report["integrity_issues"]:
        integrity_report["issues_found"] = True
        
        # Группируем рекомендации по типам проблем
        issue_types = {}
        for issue in integrity_report["integrity_issues"]:
            issue_type = issue["type"]
            if issue_type not in issue_types:
                issue_types[issue_type] = 0
            issue_types[issue_type] += 1
        
        for issue_type, count in issue_types.items():
            if issue_type == "active_table_inactive_location":
                integrity_report["recommendations"].append(
                    f"Деактивировать {count} столиков в неактивных локациях"
                )
            elif issue_type == "active_table_no_location":
                integrity_report["recommendations"].append(
                    f"Привязать {count} активных столиков к локациям или деактивировать их"
                )
            elif issue_type == "occupied_inactive_table":
                integrity_report["recommendations"].append(
                    f"Освободить {count} неактивных столиков"
                )
            elif issue_type == "order_at_inactive_table":
                integrity_report["recommendations"].append(
                    f"Завершить {count} заказов у неактивных столиков"
                )
    
    return integrity_report


async def auto_fix_integrity_issues(
    db: AsyncSession,
    fix_types: List[str] = None,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Автоматически исправляет проблемы целостности данных
    
    Args:
        db: Сессия базы данных
        fix_types: Типы проблем для исправления (None = все)
        dry_run: Если True, только показывает что будет исправлено
    
    Returns:
        Dict с результатами исправления
    """
    if fix_types is None:
        fix_types = [
            "active_table_inactive_location",
            "active_table_no_location", 
            "occupied_inactive_table",
            "order_at_inactive_table"
        ]
    
    # Сначала проверяем целостность
    integrity_report = await check_data_integrity(db)
    
    if not integrity_report["issues_found"]:
        return {
            "dry_run": dry_run,
            "fixes_applied": 0,
            "message": "Проблемы целостности не найдены"
        }
    
    fixes_applied = 0
    fixes_details = []
    
    # Получаем все столики с локациями
    tables_query = select(Table).options(selectinload(Table.location_obj))
    tables_result = await db.execute(tables_query)
    tables = tables_result.scalars().all()
    
    for table in tables:
        table_fixed = False
        fix_description = []
        
        # Исправление 1: Активный столик в неактивной локации
        if ("active_table_inactive_location" in fix_types and 
            table.is_active and table.location_obj and not table.location_obj.is_active):
            
            if not dry_run:
                table.is_active = False
                table.is_occupied = False
                table.current_order_id = None
            
            fix_description.append("деактивирован из-за неактивной локации")
            table_fixed = True
        
        # Исправление 2: Активный столик без локации
        if ("active_table_no_location" in fix_types and 
            table.is_active and not table.location_obj):
            
            if not dry_run:
                table.is_active = False
                table.is_occupied = False
                table.current_order_id = None
            
            fix_description.append("деактивирован (нет локации)")
            table_fixed = True
        
        # Исправление 3: Занятый неактивный столик
        if ("occupied_inactive_table" in fix_types and 
            table.is_occupied and not table.is_active):
            
            if not dry_run:
                table.is_occupied = False
            
            fix_description.append("освобожден (был неактивен)")
            table_fixed = True
        
        # Исправление 4: Заказ у неактивного столика
        if ("order_at_inactive_table" in fix_types and 
            table.current_order_id and not table.is_active):
            
            if not dry_run:
                table.current_order_id = None
            
            fix_description.append("сброшен активный заказ (столик неактивен)")
            table_fixed = True
        
        if table_fixed:
            fixes_applied += 1
            fixes_details.append({
                "table_id": table.id,
                "table_number": table.number,
                "location": table.location_obj.name if table.location_obj else "Без локации",
                "fixes": fix_description
            })
    
    # Сохраняем изменения (если не dry_run)
    if not dry_run and fixes_applied > 0:
        await db.commit()
        logger.info(f"Автоисправление: {fixes_applied} столиков исправлено")
    
    return {
        "dry_run": dry_run,
        "fixes_applied": fixes_applied,
        "fixes_details": fixes_details,
        "message": f"{'Будет исправлено' if dry_run else 'Исправлено'} проблем: {fixes_applied}"
    }
