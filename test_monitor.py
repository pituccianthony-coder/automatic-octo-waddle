import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Мокаем зависимости до импорта
with patch('monitor.GodfatherCore', new_callable=MagicMock) as MockCore, \
     patch('monitor.Bot', new_callable=MagicMock) as MockBot:
    from monitor import run_monitoring, WATCHLIST

@pytest.mark.asyncio
async def test_run_monitoring_sends_signal():
    """
    Тестирует, что монитор отправляет сообщение при получении сигнала 'BUY' или 'SELL'.
    """
    mock_bot = AsyncMock()
    mock_core = MagicMock()

    # Настраиваем AsyncMock с побочным эффектом, который возвращает корутины
    # Список должен быть вне функции, чтобы сохранять свое состояние между вызовами!
    results = [
        {"signal": {"signal": "HOLD"}},
        {"signal": {"signal": "HOLD"}},
        {"signal": {"signal": "BUY"}, "technicals": {"reason": "Test"}},
    ]
    async def side_effect(*args, **kwargs):
        # Возвращаем следующий результат при каждом вызове
        return results.pop(0)

    mock_core.process_symbol_for_signal = AsyncMock(side_effect=side_effect)

    # Запускаем мониторинг в задаче, которую мы можем контролировать
    monitoring_task = asyncio.create_task(run_monitoring(mock_bot, mock_core))

    # Даем задаче немного поработать, чтобы она успела сделать один цикл
    await asyncio.sleep(0.1)

    # Отменяем задачу, чтобы тест не висел вечно
    monitoring_task.cancel()
    try:
        await monitoring_task
    except asyncio.CancelledError:
        pass # Ожидаемое исключение

    # Проверяем, что анализ был вызван для всех монет в списке
    assert mock_core.process_symbol_for_signal.call_count == len(WATCHLIST)

    # Проверяем, что сообщение было отправлено только ОДИН раз (для сигнала 'BUY')
    mock_bot.send_message.assert_called_once()
    # Проверяем, что в сообщении есть нужные слова
    sent_message = mock_bot.send_message.call_args[0][1]
    assert "Proactive Signal Alert" in sent_message
    assert "BUY" in sent_message

@pytest.mark.asyncio
async def test_run_monitoring_no_signal():
    """
    Тестирует, что монитор НЕ отправляет сообщение, если все сигналы 'HOLD'.
    """
    mock_bot = AsyncMock()
    mock_core = MagicMock()

    # Настраиваем AsyncMock, который всегда возвращает одно и то же значение
    mock_core.process_symbol_for_signal = AsyncMock(return_value={"signal": {"signal": "HOLD"}})

    monitoring_task = asyncio.create_task(run_monitoring(mock_bot, mock_core))

    await asyncio.sleep(0.1)

    monitoring_task.cancel()
    try:
        await monitoring_task
    except asyncio.CancelledError:
        pass

    # Проверяем, что анализ был вызван, но сообщение НЕ было отправлено
    assert mock_core.process_symbol_for_signal.call_count == len(WATCHLIST)
    mock_bot.send_message.assert_not_called()
