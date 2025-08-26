import asyncio
from typing import Dict, Any

from config import logger, settings
from scraper import Scraper
from analyzer import Analyzer
from memory import MemoryManager

class GodfatherCore:
    """
    Центральное ядро, сердце и воля бота.
    Оркестрирует все модули: получает данные, анализирует их,
    принимает решения и сохраняет опыт.
    """

    def __init__(self):
        logger.info("Initializing Godfather Core...")
        self.scraper = Scraper()
        self.analyzer = Analyzer()
        self.memory = MemoryManager()
        self.is_shutdown = False
        logger.info("Godfather Core initialized successfully. The machine awakens.")

    async def process_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Полный цикл обработки для одного торгового символа.
        Это — основной рабочий процесс бота.
        """
        logger.info(f"--- Starting processing for symbol: {symbol} ---")
        base_currency = symbol.split('/')[0] # e.g., 'BTC' from 'BTC/USDT'

        # 1. Сбор данных (асинхронно и параллельно)
        logger.info(f"Gathering data for {symbol}...")
        tasks = {
            "klines": asyncio.create_task(self.scraper.get_binance_klines(symbol)),
            "news": asyncio.create_task(self.scraper.get_google_news_rss(base_currency))
        }
        results = await asyncio.gather(*tasks.values())

        klines_data, news_data = results[0], results[1]

        if not klines_data:
            logger.error(f"Could not retrieve kline data for {symbol}. Aborting analysis.")
            return {"error": f"Failed to get kline data for {symbol}."}

        # 2. Анализ данных
        logger.info(f"Analyzing data for {symbol}...")
        technical_analysis = self.analyzer.analyze_technicals(klines_data)
        sentiment_analysis = self.analyzer.analyze_sentiment(news_data or [])

        # 3. Генерация сигнала
        logger.info(f"Generating trade signal for {symbol}...")
        trade_signal = self.analyzer.generate_trade_signal(technical_analysis, sentiment_analysis)

        # 4. Управление памятью
        logger.info(f"Managing memory for {symbol}...")
        # Сохраняем сигнал, если он не "HOLD"
        if "HOLD" not in trade_signal['signal']:
            self.memory.add_signal(
                symbol=symbol,
                signal_type=trade_signal['signal'],
                reason=trade_signal['reason']
            )
            logger.info(f"Signal '{trade_signal['signal']}' for {symbol} was saved to memory.")

        # Сохраняем заголовки новостей в векторную память
        if news_data:
            for item in news_data[:5]: # Сохраняем только 5 самых свежих для экономии
                self.memory.add_text_memory(item['title'], source=f"news_{base_currency}")

        logger.info(f"--- Finished processing for symbol: {symbol} ---")
        return {
            "symbol": symbol,
            "signal": trade_signal,
            "technicals": technical_analysis,
            "sentiment": sentiment_analysis
        }

    async def get_chat_response(self, query: str) -> str:
        """
        Генерирует ответ на пользовательский запрос, используя контекст из памяти.
        """
        logger.info(f"Generating chat response for query: '{query}'")

        # Ищем релевантные "воспоминания" в FAISS
        memories = self.memory.search_memory(query, k=3)

        context = "Context from bot's memory:\n"
        if memories:
            for mem in memories:
                context += f"- {mem['content']} (source: {mem['metadata']['source']})\n"
        else:
            context += "- No relevant memories found.\n"

        # TODO: Интеграция с Ollama
        # Здесь будет код для отправки запроса и контекста в Ollama
        # и получения осмысленного ответа.
        # Пока что вернем заглушку.

        ollama_response = f"Ah, you ask about '{query}'. My memory tells me this:\n{context}\n(Ollama integration is pending the divine will)."
        logger.info("Generated a mock response using memory context.")

        return ollama_response


    async def shutdown(self):
        """Корректно останавливает все компоненты ядра."""
        if self.is_shutdown:
            return
        logger.info("Shutting down Godfather Core...")
        await self.scraper.close_sessions()
        self.memory.shutdown()
        self.is_shutdown = True
        logger.info("Godfather Core has been shut down.")


# Пример использования (для отладки)
async def main():
    core = GodfatherCore()
    try:
        # Тестируем обработку символа
        btc_result = await core.process_symbol('BTC/USDT')
        logger.info(f"\n--- BTC/USDT Processing Result ---\n{btc_result}\n")

        # Тестируем обработку чата
        chat_response = await core.get_chat_response("What is the news about Ethereum?")
        logger.info(f"\n--- Chat Response ---\n{chat_response}\n")

    finally:
        await core.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
