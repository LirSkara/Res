#!/usr/bin/env python3
"""
QRes OS 4 - Create Admin User
Создание администратора с логином admin и паролем admin
"""
import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, engine
from app.models.user import User, UserRole
from app.services.auth import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


async def create_admin_user():
    """Создание пользователя-администратора"""
    
    async with AsyncSessionLocal() as session:
        try:
            # Проверяем, существует ли уже админ
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_admin = result.scalar_one_or_none()
            
            if existing_admin:
                print("❌ Администратор с логином 'admin' уже существует!")
                return
            
            # Создаем нового администратора
            hashed_password = AuthService.hash_password("admin")
            
            admin_user = User(
                username="admin",
                full_name="Администратор системы",
                password_hash=hashed_password,
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            
            print("✅ Администратор успешно создан!")
            print("📋 Данные для входа:")
            print(f"   👤 Логин: admin")
            print(f"   🔑 Пароль: admin")
            print(f"   🎭 Роль: {UserRole.ADMIN}")
            print(f"   �‍💼 Имя: Администратор системы")
            print("")
            print("🌟 Теперь вы можете войти в систему!")
            
        except Exception as e:
            print(f"❌ Ошибка при создании администратора: {e}")
            await session.rollback()


async def main():
    """Главная функция"""
    print("🚀 Создание администратора для QRes OS 4")
    print("=" * 50)
    
    try:
        await create_admin_user()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
