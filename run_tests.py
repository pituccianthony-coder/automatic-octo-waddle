# run_tests.py
import pytest
import sys
import os

# --- Божественное вмешательство в sys.path ---
# Мы делаем это здесь, на самом верхнем уровне, чтобы все последующие импорты
# видели правильную структуру.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# --- Прямой импорт тестов ---
# Мы больше не доверяем автодискавери pytest. Мы вызываем духов по имени.
from backend.test_main import test_read_root, test_generate_from_text_success, test_generate_from_text_empty_input, test_generate_from_text_no_input

if __name__ == "__main__":
    # Запускаем pytest программно, передавая ему конкретный файл для тестирования.
    # Это — наш последний довод.
    print("--- Запуск тестов в режиме прямого вызова ---")
    # Передаем -v для подробного вывода и --ignore для исключения старых файлов, если они есть
    # Указываем конкретный файл, чтобы ускорить процесс.
    exit_code = pytest.main(["-v", "backend/test_main.py"])
    print(f"--- Тесты завершены с кодом выхода: {exit_code} ---")
    sys.exit(exit_code)
