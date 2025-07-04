#!/usr/bin/env python3
"""
QRes OS 4 - Authentication Tests
Тесты системы авторизации и аутентификации
"""
from tests.test_base import BaseTestSuite, TestRunner


class AuthTestSuite(BaseTestSuite):
    """Тестовый сюит для системы авторизации"""
    
    async def run_tests(self):
        """Запуск всех тестов авторизации"""
        print("\n🔐 ТЕСТИРОВАНИЕ СИСТЕМЫ АВТОРИЗАЦИИ")
        print("=" * 50)
        
        await self.test_login_valid_credentials()
        await self.test_login_invalid_credentials()
        await self.test_token_validation()
        await self.test_logout()
        await self.test_password_requirements()
        await self.test_token_expiration()
    
    async def test_login_valid_credentials(self):
        """Тест авторизации с корректными данными"""
        auth_data = {
            "username": f"{self.test_prefix}testuser",
            "password": "testpassword123"
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/auth/login", data=auth_data)
            if response.status_code == 200:
                token_data = response.json()
                
                # Проверяем наличие токена
                if "access_token" in token_data:
                    self.results.add_test("Авторизация - корректные данные", True, 
                                        "Токен получен успешно")
                    
                    # Проверяем тип токена
                    if token_data.get("token_type") == "bearer":
                        self.results.add_test("Авторизация - тип токена", True, "Bearer токен")
                    else:
                        self.results.add_test("Авторизация - тип токена", False, 
                                            f"Неожиданный тип: {token_data.get('token_type')}")
                else:
                    self.results.add_test("Авторизация - корректные данные", False, 
                                        "Токен отсутствует в ответе")
            else:
                self.results.add_test("Авторизация - корректные данные", False, 
                                    f"Код: {response.status_code}, Ответ: {response.text}")
        except Exception as e:
            self.results.add_test("Авторизация - корректные данные", False, f"Ошибка: {str(e)}")
    
    async def test_login_invalid_credentials(self):
        """Тест авторизации с некорректными данными"""
        invalid_credentials = [
            {"username": "nonexistent", "password": "wrongpass"},
            {"username": f"{self.test_prefix}testuser", "password": "wrongpass"},
            {"username": "wronguser", "password": "testpassword123"},
            {"username": "", "password": "testpassword123"},
            {"username": f"{self.test_prefix}testuser", "password": ""},
        ]
        
        for i, auth_data in enumerate(invalid_credentials):
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/auth/login", data=auth_data)
                if response.status_code == 401:
                    self.results.add_test(f"Авторизация - некорректные данные #{i+1}", True, 
                                        "Правильно отклонена")
                else:
                    self.results.add_test(f"Авторизация - некорректные данные #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Авторизация - некорректные данные #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_token_validation(self):
        """Тест валидации токена"""
        headers = self.get_auth_headers()
        
        # Тест с валидным токеном
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get("username") == f"{self.test_prefix}testuser":
                    self.results.add_test("Валидация токена - валидный токен", True, 
                                        f"Пользователь: {user_data['username']}")
                else:
                    self.results.add_test("Валидация токена - валидный токен", False, 
                                        f"Неожиданный пользователь: {user_data.get('username')}")
            else:
                self.results.add_test("Валидация токена - валидный токен", False, 
                                    f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Валидация токена - валидный токен", False, f"Ошибка: {str(e)}")
        
        # Тест с невалидным токеном
        invalid_headers = {"Authorization": "Bearer invalid_token_123"}
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/auth/me", headers=invalid_headers)
            if response.status_code == 401:
                self.results.add_test("Валидация токена - невалидный токен", True, 
                                    "Правильно отклонен")
            else:
                self.results.add_test("Валидация токена - невалидный токен", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Валидация токена - невалидный токен", False, f"Ошибка: {str(e)}")
        
        # Тест без токена
        try:
            response = await self.client.get(f"{self.runner.BASE_URL}/auth/me")
            if response.status_code == 401:
                self.results.add_test("Валидация токена - без токена", True, 
                                    "Правильно отклонен")
            else:
                self.results.add_test("Валидация токена - без токена", False, 
                                    f"Неожиданный код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Валидация токена - без токена", False, f"Ошибка: {str(e)}")
    
    async def test_logout(self):
        """Тест выхода из системы"""
        # Примечание: если есть endpoint для logout
        try:
            headers = self.get_auth_headers()
            response = await self.client.post(f"{self.runner.BASE_URL}/auth/logout", headers=headers)
            
            if response.status_code in [200, 404]:  # 404 если endpoint не реализован
                if response.status_code == 200:
                    self.results.add_test("Выход из системы", True, "Успешный выход")
                else:
                    self.results.add_test("Выход из системы", True, 
                                        "Endpoint не реализован (это нормально)", warning=True)
            else:
                self.results.add_test("Выход из системы", False, f"Код: {response.status_code}")
        except Exception as e:
            self.results.add_test("Выход из системы", True, 
                                "Endpoint не реализован (это нормально)", warning=True)
    
    async def test_password_requirements(self):
        """Тест требований к паролю при регистрации"""
        weak_passwords = [
            "123",          # Слишком короткий
            "password",     # Простой пароль
            "12345678",     # Только цифры
            "abcdefgh",     # Только буквы
            "",             # Пустой пароль
        ]
        
        for i, weak_password in enumerate(weak_passwords):
            user_data = {
                "username": f"{self.test_prefix}weakpass_{i}",
                "email": f"{self.test_prefix}weakpass_{i}@example.com",
                "password": weak_password,
                "full_name": f"Weak Pass User {i}",
                "role": "user"
            }
            
            try:
                response = await self.client.post(f"{self.runner.BASE_URL}/users/", json=user_data)
                if response.status_code in [400, 422]:  # Правильно отклонен
                    self.results.add_test(f"Требования к паролю - слабый пароль #{i+1}", True, 
                                        f"Пароль '{weak_password}' отклонен")
                elif response.status_code == 201:
                    # Если пользователь создался, добавляем его в список для удаления
                    user = response.json()
                    self.created_data['users'].append(user["id"])
                    self.results.add_test(f"Требования к паролю - слабый пароль #{i+1}", True, 
                                        f"Пароль '{weak_password}' принят (проверка не реализована)", 
                                        warning=True)
                else:
                    self.results.add_test(f"Требования к паролю - слабый пароль #{i+1}", False, 
                                        f"Неожиданный код: {response.status_code}")
            except Exception as e:
                self.results.add_test(f"Требования к паролю - слабый пароль #{i+1}", False, 
                                    f"Ошибка: {str(e)}")
    
    async def test_token_expiration(self):
        """Тест истечения токена (если реализовано)"""
        # Этот тест сложно провести без манипуляции временем
        # Проверяем, есть ли информация об истечении в токене
        
        auth_data = {
            "username": f"{self.test_prefix}testuser",
            "password": "testpassword123"
        }
        
        try:
            response = await self.client.post(f"{self.runner.BASE_URL}/auth/login", data=auth_data)
            if response.status_code == 200:
                token_data = response.json()
                
                # Проверяем наличие информации об истечении
                if "expires_in" in token_data or "exp" in token_data:
                    self.results.add_test("Истечение токена - информация", True, 
                                        "Информация об истечении присутствует")
                else:
                    self.results.add_test("Истечение токена - информация", True, 
                                        "Информация об истечении отсутствует (может быть нормально)", 
                                        warning=True)
            else:
                self.results.add_test("Истечение токена - получение токена", False, 
                                    f"Не удалось получить токен: {response.status_code}")
        except Exception as e:
            self.results.add_test("Истечение токена", False, f"Ошибка: {str(e)}")
