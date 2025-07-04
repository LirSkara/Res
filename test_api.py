#!/usr/bin/env python3
"""
QRes OS 4 - API Test Script
Скрипт для проверки всех эндпоинтов API
"""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_api():
    """Тестирование основных эндпоинтов API"""
    async with httpx.AsyncClient() as client:
        print("🧪 Тестирование QRes OS 4 API...")
        print("=" * 50)
        
        # Проверка health
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check: {data['status']} (uptime: {data['uptime']}s)")
            else:
                print(f"❌ Health Check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health Check error: {e}")
        
        # Проверка документации
        try:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print("✅ Swagger UI доступен")
            else:
                print(f"❌ Swagger UI недоступен: {response.status_code}")
        except Exception as e:
            print(f"❌ Swagger UI error: {e}")
        
        # Проверка аутентификации
        try:
            # Попытка входа с демо-данными
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            response = await client.post(
                f"{BASE_URL}/auth/login",
                data=login_data
            )
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Аутентификация работает")
                
                # Тестируем защищенный эндпоинт
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                
                # Проверка текущего пользователя
                me_response = await client.get(f"{BASE_URL}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    print(f"✅ Получен текущий пользователь: {user_data['username']}")
                
                # Проверка списка пользователей (админ)
                users_response = await client.get(f"{BASE_URL}/users/", headers=headers)
                if users_response.status_code == 200:
                    users_data = users_response.json()
                    print(f"✅ Список пользователей: {users_data['total']} пользователей")
                
                # Проверка локаций
                locations_response = await client.get(f"{BASE_URL}/locations/", headers=headers)
                if locations_response.status_code == 200:
                    locations_data = locations_response.json()
                    print(f"✅ Локации: {locations_data['total']} локаций")
                
                # Проверка категорий
                categories_response = await client.get(f"{BASE_URL}/categories/", headers=headers)
                if categories_response.status_code == 200:
                    categories_data = categories_response.json()
                    print(f"✅ Категории: {categories_data['total']} категорий")
                
                # Проверка публичного меню
                menu_response = await client.get(f"{BASE_URL}/dishes/menu")
                if menu_response.status_code == 200:
                    menu_data = menu_response.json()
                    print(f"✅ Публичное меню: {len(menu_data['categories'])} категорий")
                
                # Проверка способов оплаты
                payment_response = await client.get(f"{BASE_URL}/payment-methods/", headers=headers)
                if payment_response.status_code == 200:
                    payment_data = payment_response.json()
                    print(f"✅ Способы оплаты: {payment_data['total']} методов")
                
                # Проверка ингредиентов
                ingredients_response = await client.get(f"{BASE_URL}/ingredients/", headers=headers)
                if ingredients_response.status_code == 200:
                    ingredients_data = ingredients_response.json()
                    print(f"✅ Ингредиенты: {ingredients_data['total']} ингредиентов")
                
            else:
                print(f"❌ Аутентификация не работает: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка аутентификации: {e}")
        
        print("=" * 50)
        print("🎉 Тестирование завершено!")
        print("\n📖 Полная документация API: http://localhost:8000/docs")
        print("🔄 ReDoc документация: http://localhost:8000/redoc")

if __name__ == "__main__":
    asyncio.run(test_api())
