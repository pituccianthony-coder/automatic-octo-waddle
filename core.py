import asyncio
from typing import Dict, Any

from config import logger, settings
from scraper import Scraper
from analyzer import Analyzer
from memory import MemoryManager
from evolution import create_random_gene # Импортируем наш генератор генов

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

    async def process_symbol_with_gene(self, symbol: str, gene: dict, store_memory: bool = True) -> Dict[str, Any]:
        """
        Полный цикл обработки для одного торгового символа с использованием
        заданного "гена" (стратегии).
        """
        base_currency = symbol.split('/')[0]

        # 1. Сбор данных
        klines_data, news_data = await asyncio.gather(
            self.scraper.get_binance_klines(symbol),
            self.scraper.get_google_news_rss(base_currency)
        )

        if not klines_data:
            return {"error": f"Failed to get kline data for {symbol}."}

        # 2. Анализ данных с использованием гена
        technical_analysis = self.analyzer.analyze_technicals(klines_data, gene)
        sentiment_analysis = self.analyzer.analyze_sentiment(news_data or [])

        # 3. Генерация сигнала с использованием гена
        trade_signal = self.analyzer.generate_trade_signal(technical_analysis, sentiment_analysis, gene)

        # 4. Управление памятью (опционально, для бэктестинга можно отключать)
        if store_memory:
            if "HOLD" not in trade_signal['signal']:
                self.memory.add_signal(
                    symbol=symbol,
                    signal_type=trade_signal['signal'],
                    reason=trade_signal['reason']
                )
            if news_data:
                for item in news_data[:5]:
                    self.memory.add_text_memory(item['title'], source=f"news_{base_currency}")

        return {
            "symbol": symbol,
            "signal": trade_signal,
            "technicals": technical_analysis,
            "sentiment": sentiment_analysis,
            "gene": gene
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
        # Создаем случайный ген для демонстрации
        logger.info("--- Создание случайного гена для теста ---")
        random_gene = create_random_gene()
        logger.info(random_gene)

        # Тестируем обработку символа с этим геном
        logger.info("\n--- Тестирование обработки символа с геном ---")
        btc_result = await core.process_symbol_with_gene('BTC/USDT', random_gene)
        logger.info(f"\n--- BTC/USDT Processing Result ---\n{btc_result}\n")

    finally:
        await core.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
