#!/usr/bin/env python3
"""
QRes OS 4 - Users Tests
Тесты управления пользователями
"""
from tests.test_base import BaseTestSuite, TestRunner


class UsersTestSuite(BaseTestSuite):
    """Тестовый сюит для управления пользователями"""
    
    async def run_tests(self):
        """Запуск всех тестов пользователей"""
        print("\n👥 ТЕСТИРОВАНИЕ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ")
        print("=" * 50)
        
        await self.test_user_crud()
        await self.test_user_validation()
        await self.test_user_roles()
        await self.test_user_search()
        await self.test_user_permissions()
        await self.test_duplicate_users()
    
    async def test_user_crud(self):
        """Тест CRUD операций с пользователями"""
        create_data = {
            "username": f"{self.test_prefix}crud_user",
            "email": f"{self.test_prefix}crud@example.com",
            "password": "securepassword123",
            "full_name": f"CRUD Test User {self.test_prefix}",
            "role": "user",
            "is_active": True
        }
        
        update_data = {
            "username": f"{self.test_prefix}crud_user_updated",
            "email": f"{self.test_prefix}crud_updated@example.com",
            "full_name": f"Updated CRUD User {self.test_prefix}",
            "role": "manager",
            "is_active": True
        }
        
        required_fields = ["id", "username", "email", "full_name", "role", "is_active", "created_at"]
        
        user_id = await self.test_crud_operations(
            endpoint="users",
            create_data=create_data,
            update_data=update_data,
            data_type="users",
            required_fields=required_fields
        )
        
        return user_id
    
    async def test_user_validation(self):
        """Тест валидации данных пользователя"""
        invalid_users = [
            # Отсутствующий username
            {
                "email": f"{self.test_prefix}nousername@example.com",
                "password": "password123",
                "full_name": "No Username",
                "role": "user"
            },
            # Отсутствующий email
            {
                "username": f"{self.test_prefix}noemail",
                "password": "password123",
                "full_name": "No Email",
                "role": "user"
            },
            # Невалидный email
            {
                "username": f"{self.test_prefix}invalidemail",
                "email": "invalid-email",
                "password": "password123",
                "full_name": "Invalid Email",
                "role": "user"
            },
            # Отсутствующий пароль
            {
                "username": f"{self.test_prefix}nopass",
                "email": f"{self.test_prefix}nopass@example.com",
                "full_name": "No Password",
                "role": "user"
            },
            # Невалидная роль
            {
                "username": f"{self.test_prefix}invalidrole",
                "email": f"{self.test_prefix}invalidrole@example.com",
                "password": "password123",
                "full_name": "Invalid Role",
                "role": "invalid_role"
            }
        ]
        
        headers = self.get_auth_headers()
        
        for i, user_data in enumerate(invalid_users):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                               json=user_data, headers=headers)
                if response.status_code in [400, 422]:
                    self.results.add_test(f"Валидация пользователя #{i+1}", True, 
                                        f"Невалидные данные правильно отклонены")
                elif response.status_code == 201:
                    # Если пользователь создался, добавляем в список для удаления
                    user = response.json()
                    self.created_data['users'].append(user["id"])
                    self.results.add_test(f"Валидация пользователя #{i+1}", False, 
                                        f"Невалидные данные приняты (должны быть отклонены)")
                else:
                    self.results.add_test(f"Валидация пользователя #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Валидация пользователя #{i+1}", False, f"Ошибка: {str(e)}")
    
    async def test_user_roles(self):
        """Тест различных ролей пользователей"""
        roles = ["user", "manager", "admin"]
        headers = self.get_auth_headers()
        
        for role in roles:
            user_data = {
                "username": f"{self.test_prefix}role_{role}",
                "email": f"{self.test_prefix}role_{role}@example.com",
                "password": "password123",
                "full_name": f"Role Test {role.title()}",
                "role": role
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                               json=user_data, headers=headers)
                if response.status_code == 201:
                    user = response.json()
                    self.created_data['users'].append(user["id"])
                    
                    if user["role"] == role:
                        self.results.add_test(f"Роль пользователя - {role}", True, 
                                            f"Роль установлена корректно")
                    else:
                        self.results.add_test(f"Роль пользователя - {role}", False, 
                                            f"Роль не соответствует: ожидалось {role}, получено {user['role']}")
                else:
                    self.results.add_test(f"Роль пользователя - {role}", False, 
                                        f"Код: {response.status_code}, Ответ: {response.text}")
            except Exception as e:
                self.results.add_test(f"Роль пользователя - {role}", False, f"Ошибка: {str(e)}")
    
    async def test_user_search(self):
        """Тест поиска пользователей"""
        headers = self.get_auth_headers()
        
        # Создаем пользователей для поиска
        search_users = []
        for i in range(3):
            user_data = {
                "username": f"{self.test_prefix}search_user_{i}",
                "email": f"{self.test_prefix}search_{i}@example.com",
                "password": "password123",
                "full_name": f"Search Test User {i}",
                "role": "user"
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                               json=user_data, headers=headers)
                if response.status_code == 201:
                    user = response.json()
                    self.created_data['users'].append(user["id"])
                    search_users.append(user)
            except Exception as e:
                continue
        
        # Тест получения списка всех пользователей
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/users/", headers=headers)
            if response.status_code == 200:
                users = response.json()
                if len(users) >= len(search_users):
                    self.results.add_test("Поиск пользователей - список всех", True, 
                                        f"Получено {len(users)} пользователей")
                else:
                    self.results.add_test("Поиск пользователей - список всех", False, 
                                        f"Получено меньше пользователей чем ожидалось")
            else:
                self.results.add_test("Поиск пользователей - список всех", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Поиск пользователей - список всех", False, f"Ошибка: {str(e)}")
        
        # Тест поиска конкретного пользователя
        if search_users:
            user_id = search_users[0]["id"]
            try:
                response = await self.client.get(f"{self.runner.BASE_URL}/users/{user_id}", 
                                              headers=headers)
                if response.status_code == 200:
                    user = response.json()
                    if user["id"] == user_id:
                        self.results.add_test("Поиск пользователей - по ID", True, 
                                            f"Найден пользователь {user['username']}")
                    else:
                        self.results.add_test("Поиск пользователей - по ID", False, 
                                            f"Неверный пользователь: ожидался ID {user_id}")
                else:
                    self.results.add_test("Поиск пользователей - по ID", False, 
                                        f"Код: {response.status_code}")
            except Exception as e:
                self.results.add_test("Поиск пользователей - по ID", False, f"Ошибка: {str(e)}")
    
    async def test_user_permissions(self):
        """Тест проверки прав доступа"""
        headers = self.get_auth_headers()
        
        # Тест доступа к профилю текущего пользователя
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/users/me", headers=headers)
            if response.status_code == 200:
                user = response.json()
                if user.get("username") == f"{self.test_prefix}testuser":
                    self.results.add_test("Права доступа - свой профиль", True, 
                                        "Доступ к своему профилю получен")
                else:
                    self.results.add_test("Права доступа - свой профиль", False, 
                                        f"Неожиданный пользователь: {user.get('username')}")
            else:
                self.results.add_test("Права доступа - свой профиль", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Права доступа - свой профиль", False, f"Ошибка: {str(e)}")
        
        # Тест доступа без авторизации
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/users/")
            if response.status_code == 401:
                self.results.add_test("Права доступа - без авторизации", True, 
                                    "Доступ правильно ограничен")
            else:
                self.results.add_test("Права доступа - без авторизации", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Права доступа - без авторизации", False, f"Ошибка: {str(e)}")
    
    async def test_duplicate_users(self):
        """Тест создания дублирующихся пользователей"""
        headers = self.get_auth_headers()
        
        # Создаем первого пользователя
        user_data = {
            "username": f"{self.test_prefix}duplicate_test",
            "email": f"{self.test_prefix}duplicate@example.com",
            "password": "password123",
            "full_name": "Duplicate Test User",
            "role": "user"
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                           json=user_data, headers=headers)
            if response.status_code == 201:
                user = response.json()
                self.created_data['users'].append(user["id"])
                self.results.add_test("Дубликаты - создание первого", True, 
                                    f"Пользователь создан: {user['username']}")
                
                # Пытаемся создать дубликат с тем же username
                try:
                    duplicate_data = user_data.copy()
                    duplicate_data["email"] = f"{self.test_prefix}duplicate2@example.com"
                    
                    response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                                   json=duplicate_data, headers=headers)
                    if response.status_code in [400, 422, 409]:
                        self.results.add_test("Дубликаты - одинаковый username", True, 
                                            "Дубликат username правильно отклонен")
                    elif response.status_code == 201:
                        # Если создался, добавляем в список для удаления
                        dup_user = response.json()
                        self.created_data['users'].append(dup_user["id"])
                        self.results.add_test("Дубликаты - одинаковый username", False, 
                                            "Дубликат username был создан (не должен)")
                    else:
                        self.results.add_test("Дубликаты - одинаковый username", False, 
                                            f"Неожиданный код: {response.status_code}")
                except Exception as e:
                    self.results.add_test("Дубликаты - одинаковый username", False, 
                                        f"Ошибка: {str(e)}")
                
                # Пытаемся создать дубликат с тем же email
                try:
                    duplicate_data = user_data.copy()
                    duplicate_data["username"] = f"{self.test_prefix}duplicate_test2"
                    
                    response = await self.client.post(f"{self.runner.BASE_URL}/users/", 
                                                   json=duplicate_data, headers=headers)
                    if response.status_code in [400, 422, 409]:
                        self.results.add_test("Дубликаты - одинаковый email", True, 
                                            "Дубликат email правильно отклонен")
                    elif response.status_code == 201:
                        # Если создался, добавляем в список для удаления
                        dup_user = response.json()
                        self.created_data['users'].append(dup_user["id"])
                        self.results.add_test("Дубликаты - одинаковый email", False, 
                                            "Дубликат email был создан (не должен)")
                    else:
                        self.results.add_test("Дубликаты - одинаковый email", False, 
                                            f"Неожиданный код: {response.status_code}")
                except Exception as e:
                    self.results.add_test("Дубликаты - одинаковый email", False, 
                                        f"Ошибка: {str(e)}")
            else:
                self.results.add_test("Дубликаты - создание первого", False, 
                                    f"Код: {response.status_code}, Ответ: {response.text}")
        except Exception as e:
            self.results.add_test("Дубликаты - создание первого", False, f"Ошибка: {str(e)}")
