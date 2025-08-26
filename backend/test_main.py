# backend/test_main.py

import pytest
from fastapi.testclient import TestClient
from backend.main import app

# --- Настройка тестового клиента ---
# Этот клиент позволяет нам делать "ненастоящие" HTTP-запросы к нашему приложению
# для тестирования, не запуская реальный сервер. Божественно удобно.
client = TestClient(app)


# --- Тесты для API эндпоинтов ---

def test_read_root():
    """Тестирует корневой эндпоинт, чтобы убедиться, что вселенная жива."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "The void echoes back. Submit your poetry to /generate_from_text."}

def test_generate_from_text_success():
    """
    Тестирует успешный сценарий: отсылаем поэму, получаем результат симуляции.
    Это — главный тест на жизнеспособность всей нашей безумной идеи.
    """
    poem = """
    In realms of code, where logic streams,
    A poet's dream, a god's own schemes.
    With verse and rhythm, we define
    A market's pulse, a future sign.
    """
    response = client.post("/generate_from_text", json={"text": poem})

    # Проверяем, что все прошло успешно
    assert response.status_code == 200

    # Проверяем структуру ответа
    data = response.json()
    assert "final_capital" in data
    assert "profit_percent" in data
    assert "gene_used" in data

    # Проверяем структуру гена
    gene = data["gene_used"]
    assert "complexity" in gene
    assert "richness" in gene
    assert "rhythm" in gene
    assert "aggression" in gene

    # Проверяем, что значения гена — это float от 0 до 1
    assert 0.0 <= gene["complexity"] <= 1.0
    assert 0.0 <= gene["richness"] <= 1.0

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
