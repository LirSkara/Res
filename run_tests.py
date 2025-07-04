#!/usr/bin/env python3
"""
QRes OS 4 - Test Runner
Скрипт для запуска всех тестов
"""
import os
import sys
import subprocess

def main():
    """Запуск тестов API"""
    # Переходим в директорию с тестами
    tests_dir = os.path.join(os.path.dirname(__file__), 'tests')
    test_file = os.path.join(tests_dir, 'test_api.py')
    
    if not os.path.exists(test_file):
        print("❌ Файл тестов не найден:", test_file)
        sys.exit(1)
    
    print("🧪 Запуск тестов QRes OS 4 API...")
    print("=" * 50)
    
    try:
        # Запускаем тесты
        result = subprocess.run([sys.executable, test_file], 
                              check=False, 
                              cwd=os.path.dirname(__file__))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
