import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Перед тем как импортировать наш код, установим мок для зависимостей,
# которые могут быть тяжелыми или требовать загрузки моделей.
# Это — божественный хак, чтобы тесты были быстрыми.
import sys
mock_embeddings = MagicMock()
sys.modules['langchain_community.embeddings'] = MagicMock()
sys.modules['langchain_community.vectorstores'] = MagicMock()
sys.modules['faiss'] = MagicMock()


from core import GodfatherCore
from analyzer import Analyzer

# --- Фикстуры для тестов ---

@pytest.fixture
def mock_core():
    """Фикстура, которая создает экземпляр GodfatherCore с замоканными компонентами."""
    with patch('core.Scraper', new_callable=MagicMock) as MockScraper, \
         patch('core.Analyzer', new_callable=MagicMock) as MockAnalyzer, \
         patch('core.MemoryManager', new_callable=MagicMock) as MockMemoryManager:

        core_instance = GodfatherCore()
        core_instance.scraper = MockScraper()
        core_instance.analyzer = MockAnalyzer()
        core_instance.memory = MockMemoryManager()
        return core_instance

@pytest.fixture
def analyzer_instance():
    """Возвращает чистый экземпляр Analyzer для юнит-тестов."""
    return Analyzer()

# --- Тесты для Analyzer ---

def test_analyzer_sentiment_positive(analyzer_instance):
    """Тест на позитивный сентимент."""
    news = [{"title": "Crypto surges, everyone is happy and rich!"}]
    result = analyzer_instance.analyze_sentiment(news)
    assert result['summary'] == "POSITIVE"
    assert result['score'] > 0

def test_analyzer_sentiment_negative(analyzer_instance):
    """Тест на негативный сентимент."""
    news = [{"title": "Market crashes, total disaster, everything is lost."}]
    result = analyzer_instance.analyze_sentiment(news)
    assert result['summary'] == "NEGATIVE"
    assert result['score'] < 0

def test_analyzer_sentiment_neutral(analyzer_instance):
    """Тест на нейтральный сентимент."""
    news = [{"title": "The market is open today."}]
    result = analyzer_instance.analyze_sentiment(news)
    assert result['summary'] == "NEUTRAL"

def test_generate_signal_strong_buy(analyzer_instance):
    """Тест на генерацию сигнала STRONG_BUY."""
    tech = {"summary": "BULLISH", "reason": "RSI oversold"}
    sent = {"summary": "POSITIVE", "score": 0.9}
    signal = analyzer_instance.generate_trade_signal(tech, sent)
    assert signal['signal'] == "STRONG_BUY"

# --- Тесты для Core ---

@pytest.mark.asyncio
async def test_core_process_symbol_success(mock_core):
    """Тестирует успешный сценарий обработки символа в ядре."""
    # Настраиваем моки
    mock_core.scraper.get_binance_klines = AsyncMock(return_value=[{"close": 50000}])
    mock_core.scraper.get_google_news_rss = AsyncMock(return_value=[{"title": "BTC to the moon"}])
    mock_core.analyzer.analyze_technicals.return_value = {"summary": "BULLISH", "reason": "Magic"}
    mock_core.analyzer.analyze_sentiment.return_value = {"summary": "POSITIVE", "score": 0.8}
    mock_core.analyzer.generate_trade_signal.return_value = {"signal": "STRONG_BUY", "reason": "Because I said so"}

    symbol = "BTC/USDT"
    result = await mock_core.process_symbol(symbol)

    # Проверяем, что все было вызвано как надо
    mock_core.scraper.get_binance_klines.assert_called_once_with(symbol)
    mock_core.scraper.get_google_news_rss.assert_called_once_with("BTC")
    mock_core.analyzer.generate_trade_signal.assert_called_once()
    mock_core.memory.add_signal.assert_called_once()
    mock_core.memory.add_text_memory.assert_called_once()

    assert result['signal']['signal'] == "STRONG_BUY"

@pytest.mark.asyncio
async def test_core_process_symbol_hold_signal(mock_core):
    """Тестирует случай, когда сигнал 'HOLD' не сохраняется в память."""
    # Настраиваем моки
    mock_core.scraper.get_binance_klines = AsyncMock(return_value=[{"close": 50000}])
    mock_core.scraper.get_google_news_rss = AsyncMock(return_value=[])
    mock_core.analyzer.analyze_technicals.return_value = {"summary": "NEUTRAL", "reason": "Boring"}
    mock_core.analyzer.analyze_sentiment.return_value = {"summary": "NEUTRAL", "score": 0}
    mock_core.analyzer.generate_trade_signal.return_value = {"signal": "HOLD", "reason": "Nothing to do"}

    symbol = "ETH/USDT"
    await mock_core.process_symbol(symbol)

    # Проверяем, что add_signal НЕ был вызван
    mock_core.memory.add_signal.assert_not_called()

@pytest.mark.asyncio
async def test_core_process_symbol_scraper_fails(mock_core):
    """Тестирует случай, когда скрейпер не может получить данные."""
    # Настраиваем мок скрейпера на провал
    mock_core.scraper.get_binance_klines = AsyncMock(return_value=None)
    # Важно также замокать и второй вызов в asyncio.gather, чтобы избежать TypeError
    mock_core.scraper.get_google_news_rss = AsyncMock(return_value=[])

    symbol = "ADA/USDT"
    result = await mock_core.process_symbol(symbol)

    # Проверяем, что анализ не продолжался и была возвращена ошибка
    mock_core.analyzer.analyze_technicals.assert_not_called()
    assert "error" in result
    assert "Failed to get kline data" in result['error']
