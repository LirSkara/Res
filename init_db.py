"""
QRes OS 4 - Database Initialization Script
Скрипт для инициализации базы данных и создания демо-данных
"""
import asyncio
import sys
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import init_db, AsyncSessionLocal
from app.models import User, UserRole, Location, Category, PaymentMethod
from app.services.auth import AuthService


async def create_admin_user():
    """Создание первого администратора"""
    async with AsyncSessionLocal() as db:
        # Проверяем, есть ли уже администратор
        admin_query = select(User).where(User.role == UserRole.ADMIN)
        admin_result = await db.execute(admin_query)
        admin_user = admin_result.scalar_one_or_none()
        
        if admin_user:
            print(f"✅ Администратор уже существует: {admin_user.username}")
            return admin_user
        
        # Создаем администратора
        admin = User(
            username="admin",
            password_hash=AuthService.hash_password("admin123"),
            full_name="Системный администратор",
            role=UserRole.ADMIN,
            is_active=True,
            shift_active=False,
            pin_code="1234"
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print(f"✅ Создан администратор: {admin.username}")
        print(f"   Пароль: admin123")
        print(f"   PIN-код: 1234")
        
        return admin


async def create_demo_users(admin_user: User):
    """Создание демо-пользователей"""
    async with AsyncSessionLocal() as db:
        demo_users = [
            {
                "username": "waiter1",
                "password": "waiter123",
                "full_name": "Анна Официантова",
                "role": UserRole.WAITER,
                "pin_code": "1111",
                "phone": "+7 (900) 123-45-67"
            },
            {
                "username": "chef1", 
                "password": "chef123",
                "full_name": "Иван Поваров",
                "role": UserRole.KITCHEN,
                "pin_code": "2222",
                "phone": "+7 (900) 987-65-43"
            }
        ]
        
        for user_data in demo_users:
            # Проверяем, существует ли пользователь
            existing_query = select(User).where(User.username == user_data["username"])
            existing_result = await db.execute(existing_query)
            existing_user = existing_result.scalar_one_or_none()
            
            if existing_user:
                print(f"✅ Пользователь уже существует: {user_data['username']}")
                continue
            
            # Создаем пользователя
            new_user = User(
                username=user_data["username"],
                password_hash=AuthService.hash_password(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True,
                shift_active=False,
                pin_code=user_data["pin_code"],
                phone=user_data.get("phone"),
                created_by_id=admin_user.id
            )
            
            db.add(new_user)
            await db.commit()
            
            print(f"✅ Создан пользователь: {user_data['username']} ({user_data['role']})")


async def create_demo_locations():
    """Создание демо-локаций"""
    async with AsyncSessionLocal() as db:
        demo_locations = [
            {
                "name": "Главный зал",
                "description": "Основной зал ресторана",
                "color": "#4A90E2"
            },
            {
                "name": "Летняя веранда",
                "description": "Открытая веранда с видом на сад",
                "color": "#7ED321"
            },
            {
                "name": "VIP зона",
                "description": "Приватная зона для особых гостей",
                "color": "#F5A623"
            }
        ]
        
        for location_data in demo_locations:
            # Проверяем, существует ли локация
            existing_query = select(Location).where(Location.name == location_data["name"])
            existing_result = await db.execute(existing_query)
            existing_location = existing_result.scalar_one_or_none()
            
            if existing_location:
                print(f"✅ Локация уже существует: {location_data['name']}")
                continue
            
            # Создаем локацию
            new_location = Location(
                name=location_data["name"],
                description=location_data["description"],
                color=location_data["color"],
                is_active=True
            )
            
            db.add(new_location)
            await db.commit()
            
            print(f"✅ Создана локация: {location_data['name']}")


async def create_demo_categories():
    """Создание демо-категорий"""
    async with AsyncSessionLocal() as db:
        demo_categories = [
            {
                "name": "Салаты",
                "description": "Свежие салаты на любой вкус",
                "sort_order": 1
            },
            {
                "name": "Супы",
                "description": "Горячие и холодные супы",
                "sort_order": 2
            },
            {
                "name": "Горячие блюда",
                "description": "Основные блюда из мяса, рыбы и птицы",
                "sort_order": 3
            },
            {
                "name": "Десерты",
                "description": "Сладкие десерты и выпечка",
                "sort_order": 4
            },
            {
                "name": "Напитки",
                "description": "Горячие и холодные напитки",
                "sort_order": 5
            }
        ]
        
        for category_data in demo_categories:
            # Проверяем, существует ли категория
            existing_query = select(Category).where(Category.name == category_data["name"])
            existing_result = await db.execute(existing_query)
            existing_category = existing_result.scalar_one_or_none()
            
            if existing_category:
                print(f"✅ Категория уже существует: {category_data['name']}")
                continue
            
            # Создаем категорию
            new_category = Category(
                name=category_data["name"],
                description=category_data["description"],
                sort_order=category_data["sort_order"],
                is_active=True
            )
            
            db.add(new_category)
            await db.commit()
            
            print(f"✅ Создана категория: {category_data['name']}")


async def create_demo_payment_methods():
    """Создание демо-способов оплаты"""
    async with AsyncSessionLocal() as db:
        demo_methods = [
            {"name": "Наличные"},
            {"name": "Банковская карта"},
            {"name": "Apple Pay"},
            {"name": "Google Pay"},
            {"name": "СБП"}
        ]
        
        for method_data in demo_methods:
            # Проверяем, существует ли способ оплаты
            existing_query = select(PaymentMethod).where(PaymentMethod.name == method_data["name"])
            existing_result = await db.execute(existing_query)
            existing_method = existing_result.scalar_one_or_none()
            
            if existing_method:
                print(f"✅ Способ оплаты уже существует: {method_data['name']}")
                continue
            
            # Создаем способ оплаты
            new_method = PaymentMethod(
                name=method_data["name"],
                is_active=True
            )
            
            db.add(new_method)
            await db.commit()
            
            print(f"✅ Создан способ оплаты: {method_data['name']}")


async def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация базы данных QRes OS 4...")
    
    # Инициализируем базу данных
    await init_db()
    print("✅ База данных инициализирована")
    
    # Создаем администратора
    admin_user = await create_admin_user()
    
    # Создаем демо-данные
    await create_demo_users(admin_user)
    await create_demo_locations()
    await create_demo_categories()
    await create_demo_payment_methods()
    
    print("\n🎉 Инициализация завершена!")
    print("\n📋 Данные для входа:")
    print("   Администратор: admin / admin123 (PIN: 1234)")
    print("   Официант: waiter1 / waiter123 (PIN: 1111)")
    print("   Кухня: chef1 / chef123 (PIN: 2222)")
    print("\n🌐 Запустите сервер: uvicorn app.main:app --reload")
    print("📖 Документация API: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(main())
