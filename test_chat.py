import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Message, User, Chat

# Мокаем ядро перед импортом бота, чтобы он использовал нашу заглушку
with patch('bot.GodfatherCore', new_callable=MagicMock) as MockCore:
    from bot import handle_start, handle_help, handle_analyze, handle_latest_signals, handle_chat, core

# --- Вспомогательные функции и фикстуры ---

def create_mock_message(text: str) -> MagicMock:
    """
    Создает мок, который ведет себя как объект Message от aiogram.
    Мы не можем использовать реальный объект Message и патчить его,
    так как он является "замороженной" Pydantic-моделью.
    """
    message = MagicMock()
    message.text = text
    # aiogram v3 использует асинхронные методы, поэтому мокаем их как AsyncMock
    message.answer = AsyncMock()
    return message

@pytest_asyncio.fixture(autouse=True)
def reset_mocks():
    """Сбрасывает все моки перед каждым тестом для чистоты эксперимента."""
    # core.reset_mock() # This was incorrect as 'core' is a real instance patched at the class level
    # The mocks are implicitly reset by pytest-mock's patching mechanism per test.
    # We just need to ensure the async mocks are re-created for each test run.
    core.process_symbol = AsyncMock()
    core.get_chat_response = AsyncMock()
    core.memory.get_recent_signals = MagicMock()


# --- Тесты обработчиков команд ---

@pytest.mark.asyncio
async def test_handle_start():
    """Тестирует команду /start."""
    message = create_mock_message("/start")
    await handle_start(message)
    message.answer.assert_called_once()
    assert "The Godfather Bot is at your service" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_help():
    """Тестирует команду /help."""
    message = create_mock_message("/help")
    await handle_help(message)
    message.answer.assert_called_once()
    assert "Available Commands" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_analyze_success():
    """Тестирует успешный вызов /analyze."""
    message = create_mock_message("/analyze BTC/USDT")

    # Настраиваем мок ядра на возврат предсказуемого результата
    mock_result = {
        "symbol": "BTC/USDT",
        "signal": {"signal": "BUY", "reason": "Test reason"},
        "technicals": {"summary": "BULLISH", "reason": "Test tech reason"},
        "sentiment": {"summary": "POSITIVE", "score": 0.5}
    }
    core.process_symbol.return_value = mock_result

    await handle_analyze(message)

    # Проверяем, что ядро было вызвано с правильным символом
    core.process_symbol.assert_called_once_with("BTC/USDT")

    # Проверяем, что бот ответил дважды (сначала 'Analyzing...', потом результат)
    assert message.answer.call_count == 2
    final_response = message.answer.call_args_list[1][0][0]
    assert "Analysis for BTC/USDT" in final_response
    assert "Final Signal: BUY" in final_response

@pytest.mark.asyncio
async def test_handle_analyze_no_symbol():
    """Тестирует вызов /analyze без символа."""
    message = create_mock_message("/analyze")
    await handle_analyze(message)
    message.answer.assert_called_once_with("Please specify a symbol. Usage: <code>/analyze BTC/USDT</code>")
    core.process_symbol.assert_not_called()

@pytest.mark.asyncio
async def test_handle_latest_signals():
    """Тестирует команду /latest_signals."""
    message = create_mock_message("/latest_signals")

    # Настраиваем мок памяти
    mock_signals = [
        {"symbol": "BTC/USDT", "signal_type": "BUY", "timestamp": MagicMock(), "reason": "R1"},
        {"symbol": "ETH/USDT", "signal_type": "SELL", "timestamp": MagicMock(), "reason": "R2"},
    ]
    mock_signals[0]['timestamp'].strftime.return_value = "2025-01-01 12:00"
    mock_signals[1]['timestamp'].strftime.return_value = "2025-01-01 13:00"
    core.memory.get_recent_signals.return_value = mock_signals

    await handle_latest_signals(message)

    core.memory.get_recent_signals.assert_called_once_with(limit=5)
    message.answer.assert_called_once()
    response_text = message.answer.call_args[0][0]
    # The response contains HTML tags, so we must assert against them
    assert "<b>BTC/USDT</b> - BUY" in response_text
    assert "<b>ETH/USDT</b> - SELL" in response_text

@pytest.mark.asyncio
async def test_handle_chat():
    """Тестирует обработчик свободных текстовых сообщений."""
    message = create_mock_message("Tell me about Bitcoin")
    core.get_chat_response.return_value = "Bitcoin is a decentralized digital currency."

    await handle_chat(message)

    core.get_chat_response.assert_called_once_with("Tell me about Bitcoin")

    # Проверяем, что бот ответил дважды ('Thinking...', потом результат)
    assert message.answer.call_count == 2
    final_response = message.answer.call_args_list[1][0][0]
    assert final_response == "Bitcoin is a decentralized digital currency."
