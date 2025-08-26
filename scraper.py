import asyncio
import ccxt.async_support as ccxt
import httpx
import feedparser
from typing import List, Dict, Any, Optional

from config import settings, logger

class Scraper:
    """
    Всевидящее око нашего бота.
    Этот класс асинхронно собирает данные из различных источников:
    - Binance: для точных рыночных данных (свечи).
    - Google News: для анализа настроений и поиска инсайтов.
    - CoinGecko: для отслеживания общих трендов рынка.
    """

    def __init__(self):
        logger.info("Initializing Scraper...")
        self.http_client = httpx.AsyncClient(timeout=15.0)

        # Инициализация CCXT для Binance
        self.binance = ccxt.binance({
            'apiKey': settings.BINANCE_API_KEY,
            'secret': settings.BINANCE_API_SECRET,
            'options': {
                'defaultType': 'spot',
            },
            'enableRateLimit': True,
        })
        logger.info("Scraper initialized successfully.")

    async def close_sessions(self):
        """Закрывает все открытые сессии. Божественная чистота и порядок."""
        await self.http_client.aclose()
        await self.binance.close()
        logger.info("Scraper sessions closed gracefully.")

    async def get_binance_klines(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Получает исторические данные о свечах (OHLCV) с Binance.
        """
        logger.info(f"Fetching {limit} klines for {symbol} with timeframe {timeframe} from Binance.")
        try:
            # CCXT возвращает список списков, преобразуем его в более читаемый формат
            klines = await self.binance.fetch_ohlcv(symbol, timeframe, limit=limit)
            structured_klines = [
                {
                    "timestamp": kline[0],
                    "open": kline[1],
                    "high": kline[2],
                    "low": kline[3],
                    "close": kline[4],
                    "volume": kline[5]
                }
                for kline in klines
            ]
            return structured_klines
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol} from Binance: {e}")
            return None

    async def get_google_news_rss(self, query: str, lang: str = 'en', country: str = 'US') -> Optional[List[Dict[str, str]]]:
        """
        Получает новости через RSS-фид Google News.
        Древний, но надежный способ слушать эхо мира.
        """
        logger.info(f"Fetching Google News RSS for query: '{query}'")
        url = f"https://news.google.com/rss/search?q={query}&hl={lang}&gl={country}&ceid={country}:{lang}"
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()

            feed = feedparser.parse(response.text)
            news_items = [
                {
                    "title": entry.title,
                    "link": entry.link,
                    "published": entry.published,
                    "summary": entry.summary
                }
                for entry in feed.entries
            ]
            return news_items
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching Google News for '{query}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse Google News feed for '{query}': {e}")
            return None

    async def get_coingecko_trending(self) -> Optional[Dict]:
        """
        Получает список трендовых монет с CoinGecko.
        Ощущаем пульс рынка.
        """
        # CoinGecko имеет бесплатный API, но для продакшена лучше использовать Pro с ключом
        if not settings.COINGECKO_API_KEY:
            logger.warning("Using CoinGecko's free API. Rate limits may apply.")
            url = "https://api.coingecko.com/api/v3/search/trending"
            headers = {}
        else:
            logger.info("Using CoinGecko Pro API.")
            url = "https://pro-api.coingecko.com/api/v3/search/trending"
            headers = {"x-cg-pro-api-key": settings.COINGECKO_API_KEY}

        try:
            response = await self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"HTTP error fetching CoinGecko trending data: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse CoinGecko response: {e}")
            return None


# Пример использования (для отладки)
async def main():
    logger.info("--- Running Scraper standalone test ---")
    scraper = Scraper()

    # Тест Binance
    btc_klines = await scraper.get_binance_klines('BTC/USDT')
    if btc_klines:
        logger.info(f"Successfully fetched {len(btc_klines)} klines for BTC/USDT. Last close: {btc_klines[-1]['close']}")
        assert len(btc_klines) > 0

    # Тест Google News
    crypto_news = await scraper.get_google_news_rss("Bitcoin")
    if crypto_news:
        logger.info(f"Successfully fetched {len(crypto_news)} news items for 'Bitcoin'. First title: {crypto_news[0]['title']}")
        assert len(crypto_news) > 0

    # Тест CoinGecko
    trending_coins = await scraper.get_coingecko_trending()
    if trending_coins:
        logger.info(f"Successfully fetched {len(trending_coins.get('coins', []))} trending coins.")
        assert 'coins' in trending_coins

    await scraper.close_sessions()
    logger.info("--- Standalone test completed successfully ---")

if __name__ == '__main__':
    # Для запуска асинхронного main
    asyncio.run(main())
