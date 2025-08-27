import pytest
from fastapi.testclient import TestClient
import sys
import os

# Добавляем корневую директорию в путь, чтобы импорт 'backend' работал
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app

client = TestClient(app)

def test_read_root():
    """Тестирует корневой эндпоинт."""
    response = client.get("/")
    assert response.status_code == 200
    assert "The sanctuary is silent" in response.json()["message"]

def test_generate_insight_success():
    """Тестирует успешный вызов эндпоинта /generate_insight."""
    test_text = "This is a simple test sentence. It has a certain rhythm."
    response = client.post("/generate_insight", json={"text": test_text})

    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recommended_action" in data
    assert "gene_used" in data
    assert "complexity" in data["gene_used"]

def test_generate_insight_empty_text():
    """Тестирует обработку пустого ввода."""
    response = client.post("/generate_insight", json={"text": ""})
    assert response.status_code == 400
    assert "Text input cannot be empty" in response.json()["detail"]

def test_generate_insight_bad_payload():
    """Тестирует обработку неправильного формата данных."""
    response = client.post("/generate_insight", json={"not_text": "hello"})
    assert response.status_code == 422 # Unprocessable Entity
