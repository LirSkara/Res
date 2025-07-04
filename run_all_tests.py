#!/usr/bin/env python3
"""
QRes OS 4 - Complete Test Suite Runner
Запуск всех модульных тестов с полной детализацией
"""
import asyncio
import time
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


async def run_complete_test_suite():
    """Запуск полного комплекта тестов"""
    print("🧪 QRes OS 4 - ПОЛНЫЙ КОМПЛЕКТ ТЕСТОВ")
    print("=" * 70)
    print(f"⏰ Начало тестирования: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Инициализация тест-раннера
    runner = TestRunner()
    await runner.setup()
    
    # Список всех тестовых сюитов
    test_suites = [
        ("🔐 Авторизация", AuthTestSuite),
        ("👥 Пользователи", UsersTestSuite),
        ("📍 Локации", LocationsTestSuite),
        ("🪑 Столы", TablesTestSuite),
        ("📂 Категории", CategoriesTestSuite),
        ("🍽️ Блюда", DishesTestSuite),
        ("🎛️ Вариации блюд", DishVariationsTestSuite),
        ("🥕 Ингредиенты", IngredientsTestSuite),
        ("💳 Способы оплаты", PaymentMethodsTestSuite),
        ("📋 Заказы", OrdersTestSuite),
        ("📝 Элементы заказа", OrderItemsTestSuite),
    ]
    
    all_results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_warnings = 0
    
    # Запуск каждого тестового сюита
    for suite_name, suite_class in test_suites:
        print(f"\n{suite_name}")
        print("-" * 50)
        
        try:
            suite = suite_class(runner)
            await suite.run_tests()
            
            # Подсчет результатов
            passed = len([t for t in suite.results.tests if t["passed"]])
            failed = len([t for t in suite.results.tests if not t["passed"] and not t.get("warning", False)])
            warnings = len([t for t in suite.results.tests if t.get("warning", False)])
            
            total_tests += len(suite.results.tests)
            total_passed += passed
            total_failed += failed
            total_warnings += warnings
            
            all_results.append({
                "name": suite_name,
                "results": suite.results,
                "passed": passed,
                "failed": failed,
                "warnings": warnings
            })
            
            # Отображение результатов текущего сюита
            suite.results.print_results()
            
        except Exception as e:
            print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в {suite_name}: {str(e)}")
            total_failed += 1
    
    # Финальный отчет
    print("\n" + "=" * 70)
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ")
    print("=" * 70)
    
    for result in all_results:
        status = "✅" if result["failed"] == 0 else "❌"
        warning_text = f" (⚠️ {result['warnings']} предупреждений)" if result["warnings"] > 0 else ""
        print(f"{status} {result['name']}: {result['passed']}/{result['passed'] + result['failed']} тестов прошло{warning_text}")
    
    print("\n" + "-" * 70)
    print(f"📈 ОБЩАЯ СТАТИСТИКА:")
    print(f"   Всего тестов: {total_tests}")
    print(f"   ✅ Прошло: {total_passed}")
    print(f"   ❌ Не прошло: {total_failed}")
    print(f"   ⚠️ Предупреждения: {total_warnings}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"   📊 Процент успеха: {success_rate:.1f}%")
    
    print(f"\n⏰ Окончание тестирования: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Финальная очистка
    await runner.teardown()
    
    # Возврат результата
    if total_failed == 0:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return True
    else:
        print(f"\n💥 ТЕСТИРОВАНИЕ ЗАВЕРШИЛОСЬ С ОШИБКАМИ: {total_failed} неудачных тестов")
        return False


if __name__ == "__main__":
    import sys
    success = asyncio.run(run_complete_test_suite())
    sys.exit(0 if success else 1)
