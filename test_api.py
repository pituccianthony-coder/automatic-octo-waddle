import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Mock heavy dependencies before import
import sys
sys.modules['langchain_community.embeddings'] = MagicMock()
sys.modules['langchain_community.vectorstores'] = MagicMock()
sys.modules['faiss'] = MagicMock()

from core import GodfatherCore
from analyzer import Analyzer

@pytest.fixture
def mock_core():
    with patch('core.Scraper', new_callable=MagicMock) as MockScraper, \
         patch('core.Analyzer', new_callable=MagicMock) as MockAnalyzer, \
         patch('core.MemoryManager', new_callable=MagicMock) as MockMemoryManager:

        core_instance = GodfatherCore()
        core_instance.scraper = MockScraper()
        core_instance.analyzer = MockAnalyzer()
        core_instance.memory = MockMemoryManager()
        return core_instance

@pytest.mark.asyncio
async def test_core_process_symbol_success(mock_core):
    """Tests the successful processing of a symbol for a signal."""
    mock_core.scraper.get_klines = AsyncMock(return_value=[{"close": 50000}])
    mock_core.analyzer.analyze_technicals.return_value = {"summary": "BULLISH", "reason": "Magic"}
    mock_core.analyzer.generate_trade_signal.return_value = {"signal": "BUY", "reason": "Because I said so"}

    symbol = "BTC/USDT"
    result = await mock_core.process_symbol_for_signal(symbol)

    mock_core.scraper.get_klines.assert_called_once_with(symbol)
    mock_core.analyzer.generate_trade_signal.assert_called_once()
    mock_core.memory.add_signal.assert_called_once()
    assert result['signal']['signal'] == "BUY"

@pytest.mark.asyncio
async def test_core_process_symbol_hold(mock_core):
    """Tests that a HOLD signal is not saved to memory."""
    mock_core.scraper.get_klines = AsyncMock(return_value=[{"close": 50000}])
    mock_core.analyzer.analyze_technicals.return_value = {"summary": "NEUTRAL", "reason": "Boring"}
    mock_core.analyzer.generate_trade_signal.return_value = {"signal": "HOLD", "reason": "Patience"}

    symbol = "ETH/USDT"
    await mock_core.process_symbol_for_signal(symbol)

    mock_core.memory.add_signal.assert_not_called()
