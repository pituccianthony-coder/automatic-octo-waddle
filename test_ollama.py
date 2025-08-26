import pytest
from unittest.mock import patch, AsyncMock

from ollama_manager import OllamaManager

@pytest.mark.asyncio
async def test_ollama_manager_success():
    """
    Тестирует успешный ответ от OllamaManager, мокая реальный вызов API.
    """
    # Создаем мок для AsyncClient
    with patch('ollama.AsyncClient') as MockAsyncClient:
        # Настраиваем мок, чтобы он возвращал ожидаемый ответ
        mock_instance = MockAsyncClient.return_value
        mock_instance.chat = AsyncMock(return_value={
            'message': {
                'content': 'This is a wise answer from the oracle.'
            }
        })

        manager = OllamaManager()
        prompt = "What is the meaning of life?"
        context = "The user is a philosopher."

        response = await manager.get_chat_response(prompt, context)

        # Проверяем, что ответ правильный
        assert response == 'This is a wise answer from the oracle.'

        # Проверяем, что метод chat был вызван
        mock_instance.chat.assert_called_once()
        call_args = mock_instance.chat.call_args
        # Проверяем, что промпт был правильно сформирован
        assert "System Prompt:" in call_args.kwargs['messages'][0]['content']
        assert prompt in call_args.kwargs['messages'][0]['content']
        assert context in call_args.kwargs['messages'][0]['content']

@pytest.mark.asyncio
async def test_ollama_manager_api_failure():
    """
    Тестирует, как менеджер обрабатывает ошибку при вызове API.
    """
    with patch('ollama.AsyncClient') as MockAsyncClient:
        # Настраиваем мок, чтобы он вызывал исключение
        mock_instance = MockAsyncClient.return_value
        mock_instance.chat = AsyncMock(side_effect=Exception("Connection refused"))

        manager = OllamaManager()
        response = await manager.get_chat_response("test", "test")

        # Проверяем, что возвращается сообщение об ошибке
        assert "The oracle is silent" in response
