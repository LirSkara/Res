import asyncio
from app.database import AsyncSessionLocal
from app.models import Location, Table
from sqlalchemy import select

LOCATION_NAME = "Основной зал"

async def deactivate_location_and_check_tables():
    async with AsyncSessionLocal() as db:
        # 1. Найти локацию по имени
        loc_query = select(Location).where(Location.name == LOCATION_NAME)
        loc_result = await db.execute(loc_query)
        location = loc_result.scalar_one_or_none()
        if not location:
            print(f"Локация '{LOCATION_NAME}' не найдена!")
            return
        print(f"Локация: {location.id} - {location.name} (is_active={location.is_active})")

        # 2. Деактивировать локацию
        if location.is_active:
            location.is_active = False
            await db.commit()
            await db.refresh(location)
            print(f"Локация '{location.name}' деактивирована!")
        else:
            print(f"Локация '{location.name}' уже неактивна.")

        # 3. Проверить статусы столиков
        tables_query = select(Table).where(Table.location_id == location.id)
        tables_result = await db.execute(tables_query)
        tables = tables_result.scalars().all()
        print(f"Столики в локации '{location.name}': {len(tables)}")
        for t in tables:
            print(f"  Столик {t.number}: is_active={t.is_active}, is_occupied={t.is_occupied}, current_order_id={t.current_order_id}")

if __name__ == "__main__":
    asyncio.run(deactivate_location_and_check_tables())
