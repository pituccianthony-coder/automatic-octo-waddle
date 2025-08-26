# ollama_manager.py

import ollama
from config import settings, logger

class OllamaManager:
    """
    Менеджер для общения с локальным оракулом — Ollama.
    Он переводит наши вопросы в запросы к LLM и возвращает мудрость.
    """

    def __init__(self):
        self.client = ollama.AsyncClient(host=settings.OLLAMA_HOST)
        logger.info(f"OllamaManager initialized for model: {settings.OLLAMA_MODEL}")

    async def get_chat_response(self, prompt: str, context: str) -> str:
        """
        Отправляет промпт и контекст в Ollama и возвращает стриминговый ответ.
        """
        full_prompt = f"""
        System Prompt: You are a concise and insightful trading assistant integrated into a Telegram bot.
        A user has asked a question. Use the provided context from your memory to answer it.
        If the context is irrelevant, ignore it. Keep your answers short and to the point.

        Context from memory:
        {context}

        User's question: "{prompt}"

        Your answer:
        """

        try:
            logger.info("Sending request to Ollama...")
            response = await self.client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': full_prompt}]
            )
            logger.info("Received response from Ollama.")
            return response['message']['content']
        except Exception as e:
            logger.error(f"Failed to get response from Ollama: {e}")
            return "The oracle is silent at the moment. A connection could not be established."

# --- Демонстрация ---
async def main():
    import asyncio
    manager = OllamaManager()
    test_prompt = "What is the general sentiment around Bitcoin right now?"
    test_context = "- User previously asked about Ethereum.\n- A recent news headline was 'Bitcoin surges past new highs'."
    response = await manager.get_chat_response(test_prompt, test_context)
    print("--- Ollama Manager Test ---")
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
