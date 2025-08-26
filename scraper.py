import asyncio
import ccxt.async_support as ccxt
import httpx
from typing import List, Dict, Any, Optional

from config import settings, logger

class Scraper:
    """
    Всевидящее око нашего бота.
    Этот класс асинхронно собирает данные из различных источников.
    """

    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=15.0)
        self.binance = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'enableRateLimit': True,
        })

    async def close_sessions(self):
        await self.http_client.aclose()
        await self.binance.close()

    def _structure_klines(self, klines: List) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": kline[0], "open": kline[1], "high": kline[2],
                "low": kline[3], "close": kline[4], "volume": kline[5]
            }
            for kline in klines
        ]

    async def get_klines(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        logger.info(f"Fetching {limit} klines for {symbol}...")
        try:
            klines = await self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
            return self._structure_klines(klines)
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
