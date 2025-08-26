# backend/test_main.py

import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# // Божественный хак, чтобы исправить запутанные пути Python в этой песочнице.
# // Мы вручную добавляем корневую директорию проекта в sys.path.
# // Не пытайтесь повторить это в чистом продакшене, если вы не бог.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Мокаем зависимости ПЕРЕД импортом app, чтобы он подхватил наши моки
with patch('backend.main.Poet') as MockPoet, \
     patch('backend.main.simulate_market') as MockSimulateMarket, \
     patch('backend.core.Web3Manager') as MockWeb3Manager:

    # Настраиваем возвращаемые значения для моков
    MockSimulateMarket.return_value = {
        "initial_capital": 1000.0, "final_capital": 1100.0,
        "profit": 100.0, "profit_percent": 10.0, "gene_used": {"test": "gene"}
    }

    from backend.main import app
    client = TestClient(app)


# --- Тесты для API эндпоинтов ---

@patch('backend.core.Web3Manager')
def test_read_root(MockWeb3Manager): # Передаем мок, чтобы он был активен
    response = client.get("/")
    assert response.status_code == 200
    assert "Submit your poetry" in response.json()["message"]

@patch('backend.core.Web3Manager')
@patch('backend.main.simulate_market')
@patch('backend.main.Poet')
def test_generate_from_text_success(MockPoet, MockSimulateMarket, MockWeb3Manager):
    """
    Тестирует успешный сценарий, мокая все зависимости, чтобы проверить
    только логику эндпоинта и вызовы ядра.
    """
    # Настраиваем моки для этого конкретного теста
    mock_poet_instance = MockPoet.return_value
    mock_poet_instance.text_to_gene.return_value = {"test": "gene"}

    MockSimulateMarket.return_value = {
        "initial_capital": 1000.0, "final_capital": 1100.0,
        "profit": 100.0, "profit_percent": 10.0, "gene_used": {"test": "gene"}
    }

    mock_web3_instance = MockWeb3Manager.return_value

    # Выполняем запрос
    response = client.post("/generate_from_text", json={"text": "some poetry"})

    # Проверяем, что все прошло успешно
    assert response.status_code == 200

    # Проверяем, что наши моки были вызваны
    mock_poet_instance.text_to_gene.assert_called_once_with("some poetry")
    MockSimulateMarket.assert_called_once_with({"test": "gene"})

    # Проверяем, что ядро вызвало методы web3_manager
    # Так как профит > 0, должен быть вызван депозит
    mock_web3_instance.deposit_to_dao.assert_called_once()
    mock_web3_instance.execute_swap.assert_called_once()

def test_generate_from_text_empty_input():
    """Тестирует, что API корректно обрабатывает пустой ввод."""
    response = client.post("/generate_from_text", json={"text": ""})
    # Ожидаем ошибку 400 Bad Request
    assert response.status_code == 400
    assert "Text cannot be empty" in response.json()["detail"]

def test_generate_from_text_no_input():
    """Тестирует, что API корректно обрабатывает неправильный формат JSON."""
    response = client.post("/generate_from_text", json={"wrong_key": "some text"})
    # Ожидаем ошибку 422 Unprocessable Entity, так как поле 'text' отсутствует
    assert response.status_code == 422

# // Здесь можно было бы добавить еще тестов, например, на граничные случаи в NLP,
# // но для доказательства концепции этого более чем достаточно.
# // Мы же не хотим, чтобы наше творение стало слишком предсказуемым, верно?
