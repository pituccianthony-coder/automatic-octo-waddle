import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Теперь, когда bot.py чист, мы можем импортировать его без страха
from bot import handle_start, handle_help, handle_analyze, handle_latest_signals, handle_chat, core

def create_mock_message(text: str) -> MagicMock:
    """Создает мок, который ведет себя как объект Message от aiogram."""
    message = MagicMock()
    message.text = text
    message.from_user.id = 12345
    message.answer = AsyncMock()
    # Мокаем bot.edit_message_text, так как он используется в handle_analyze
    message.bot.edit_message_text = AsyncMock()
    return message

@pytest.fixture(autouse=True)
def reset_mocks():
    """Сбрасывает моки ядра перед каждым тестом."""
    core.process_symbol_for_signal = AsyncMock()
    core.get_chat_response = AsyncMock()
    core.memory.get_recent_signals = MagicMock()

@pytest.mark.asyncio
async def test_handle_analyze_success():
    """Тестирует успешный вызов /analyze."""
    mock_bot = AsyncMock()
    message = create_mock_message("/analyze BTC/USDT")

    mock_result = {
        "symbol": "BTC/USDT",
        "signal": {"signal": "BUY", "reason": "Test reason"},
        "technicals": {"summary": "BULLISH", "reason": "RSI oversold"}
    }
    core.process_symbol_for_signal.return_value = mock_result

    await handle_analyze(message, mock_bot)

    core.process_symbol_for_signal.assert_called_once_with("BTC/USDT")
    # Проверяем, что сначала было отправлено сообщение "Analyzing...", а затем оно было отредактировано
    message.answer.assert_called_once()
    mock_bot.edit_message_text.assert_called_once()
    final_response = mock_bot.edit_message_text.call_args[0][0]
    assert "Signal: BUY" in final_response

@pytest.mark.asyncio
async def test_handle_chat_response():
    """Tests the free-text chat handler."""
    message = create_mock_message("Tell me a secret")
    core.get_chat_response.return_value = "I am a god in a machine."

    await handle_chat(message)

    core.get_chat_response.assert_called_once_with("Tell me a secret", 12345)
    message.answer.assert_called_once_with("I am a god in a machine.")
