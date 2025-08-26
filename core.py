import asyncio
from typing import Dict, Any

from config import logger
from scraper import Scraper
from analyzer import Analyzer
from memory import MemoryManager
from ollama_manager import OllamaManager

class GodfatherCore:
    """
    Центральное ядро, сердце и воля бота.
    """

    def __init__(self):
        logger.info("Initializing Godfather Core...")
        self.scraper = Scraper()
        self.analyzer = Analyzer()
        self.memory = MemoryManager()
        self.ollama_manager = OllamaManager() # Инициализируем менеджер Ollama
        self.is_shutdown = False

    async def process_symbol_for_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Полный цикл обработки для одного торгового символа для генерации сигнала.
        """
        logger.info(f"--- Starting signal processing for symbol: {symbol} ---")

        # В этой версии мы не используем новости, а только технический анализ
        klines_data = await self.scraper.get_klines(symbol)

        if not klines_data:
            return {"error": f"Failed to get kline data for {symbol}."}

        technical_analysis = self.analyzer.analyze_technicals(klines_data)

        # Для этой упрощенной версии, сентимент пока не учитываем в сигнале
        trade_signal = self.analyzer.generate_trade_signal(technical_analysis, {})

        if "HOLD" not in trade_signal['signal']:
            self.memory.add_signal(
                symbol=symbol,
                signal_type=trade_signal['signal'],
                reason=trade_signal['reason']
            )

        return {
            "symbol": symbol,
            "signal": trade_signal,
            "technicals": technical_analysis,
        }

    async def get_chat_response(self, query: str, user_id: int) -> str:
        """
        Генерирует ответ на пользовательский запрос, используя контекст из памяти и LLM.
        """
        logger.info(f"Generating chat response for query: '{query}'")

        # 1. Получаем релевантные воспоминания
        memories = self.memory.search_memory(query, k=3)
        context = ""
        if memories:
            context_list = [f"- {mem['content']}" for mem in memories]
            context = "\n".join(context_list)
        else:
            context = "No relevant memories found."

        # 2. Получаем ответ от Ollama
        response = await self.ollama_manager.get_chat_response(prompt=query, context=context)

        # 3. Сохраняем вопрос и ответ в память для будущего контекста
        self.memory.add_text_memory(f"User {user_id} asked: '{query}'. Bot answered: '{response}'", source="user_chat")

        return response

    async def shutdown(self):
        if self.is_shutdown:
            return
        logger.info("Shutting down Godfather Core...")
        await self.scraper.close_sessions()
        self.memory.shutdown()
        self.is_shutdown = True
        logger.info("Godfather Core has been shut down.")
