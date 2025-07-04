#!/usr/bin/env python3
"""
QRes OS 4 - Pytest Test Runner
Pytest-совместимые обертки для всех модульных тестов
"""
import pytest
import asyncio
from tests.test_base import TestRunner

# Импорт всех тестовых сюитов
from tests.test_auth import AuthTestSuite
from tests.test_users import UsersTestSuite
from tests.test_locations import LocationsTestSuite
from tests.test_tables import TablesTestSuite
from tests.test_categories import CategoriesTestSuite
from tests.test_dishes import DishesTestSuite
from tests.test_dish_variations import DishVariationsTestSuite
from tests.test_ingredients import IngredientsTestSuite
from tests.test_payment_methods import PaymentMethodsTestSuite
from tests.test_orders import OrdersTestSuite
from tests.test_order_items import OrderItemsTestSuite


@pytest.mark.asyncio
async def test_auth_module():
    """Тест модуля авторизации"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = AuthTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Auth tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_users_module():
    """Тест модуля пользователей"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = UsersTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"User tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_locations_module():
    """Тест модуля локаций"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = LocationsTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Location tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_tables_module():
    """Тест модуля столов"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = TablesTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Table tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_categories_module():
    """Тест модуля категорий"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = CategoriesTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Category tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_dishes_module():
    """Тест модуля блюд"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = DishesTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Dish tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_dish_variations_module():
    """Тест модуля вариаций блюд"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = DishVariationsTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Dish variation tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_ingredients_module():
    """Тест модуля ингредиентов"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = IngredientsTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Ingredient tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_payment_methods_module():
    """Тест модуля способов оплаты"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = PaymentMethodsTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Payment method tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_orders_module():
    """Тест модуля заказов"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = OrdersTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Order tests failed:\n{error_msg}")
    
    await runner.teardown()


@pytest.mark.asyncio
async def test_order_items_module():
    """Тест модуля элементов заказа"""
    runner = TestRunner()
    await runner.setup()
    
    test_suite = OrderItemsTestSuite(runner)
    await test_suite.run_tests()
    
    # Проверяем результаты
    failed_tests = [test for test in test_suite.results.tests if not test["passed"]]
    if failed_tests:
        error_msg = "\n".join([f"❌ {test['name']}: {test['message']}" for test in failed_tests])
        pytest.fail(f"Order item tests failed:\n{error_msg}")
    
    await runner.teardown()
