import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, BotCommand
from aiogram.enums import ParseMode

from config import settings, logger
from core import GodfatherCore

# --- Инициализация ---
# Создаем объекты Бота, Диспетчера и нашего Ядра.
# Это святая троица нашего приложения.
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
core = GodfatherCore()

# --- Команды для меню ---
async def set_main_menu(bot: Bot):
    """Создает кнопку 'Меню' со списком команд."""
    main_menu_commands = [
        BotCommand(command="/analyze", description="Анализ символа (напр. /analyze BTC/USDT)"),
        BotCommand(command="/latest_signals", description="Показать последние 5 сигналов"),
        BotCommand(command="/help", description="Справка по боту"),
    ]
    await bot.set_my_commands(main_menu_commands)

# --- Обработчики команд ---

@dp.message(Command("start"))
async def handle_start(message: Message):
    """Обработчик команды /start. Приветствие."""
    await message.answer(
        "<b>The Godfather Bot is at your service.</b>\n\n"
        "I see the world in numbers, news, and sentiment. I am here to analyze and report.\n"
        "Use /analyze [SYMBOL] (e.g., <code>/analyze BTC/USDT</code>) to get my insights.\n"
        "Use /help to see all my capabilities."
    )

@dp.message(Command("help"))
async def handle_help(message: Message):
    """Обработчик команды /help. Помощь по командам."""
    await message.answer(
        "<b>Available Commands:</b>\n\n"
        "<code>/analyze [SYMBOL]</code> - Provides a full analysis for a trading pair (e.g., BTC/USDT, ETH/USDT).\n\n"
        "<code>/latest_signals</code> - Shows the last 5 non-HOLD signals generated.\n\n"
        "Simply chat with me to get AI-powered responses based on my knowledge."
    )

@dp.message(Command("analyze"))
async def handle_analyze(message: Message):
    """
    Обработчик команды /analyze.
    Запускает ядро для анализа и отправляет результат.
    """
    symbol = message.text.split()[1] if len(message.text.split()) > 1 else None
    if not symbol:
        await message.answer("Please specify a symbol. Usage: <code>/analyze BTC/USDT</code>")
        return

    symbol = symbol.upper()
    await message.answer(f"Analyzing {symbol}... This may take a moment, the gears of intellect are turning.")

    try:
        result = await core.process_symbol(symbol)
        if "error" in result:
            await message.answer(f"<b>Analysis failed:</b> {result['error']}")
            return

        # Форматируем красивый ответ
        response_text = (
            f"<b>Analysis for {result['symbol']}</b>\n\n"
            f"<b><u>Final Signal: {result['signal']['signal']}</u></b>\n"
            f"<i>Reason: {result['signal']['reason']}</i>\n\n"
            f"<b>Technical Summary:</b> {result['technicals']['summary']}\n"
            f"<i>Details: {result['technicals']['reason']}</i>\n\n"
            f"<b>Sentiment Summary:</b> {result['sentiment']['summary']} (Score: {result['sentiment']['score']:.2f})"
        )
        await message.answer(response_text)

    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis for {symbol}: {e}")
        await message.answer("A critical error occurred. The divine machine is displeased. Check logs.")

@dp.message(Command("latest_signals"))
async def handle_latest_signals(message: Message):
    """Показывает последние сигналы из памяти."""
    signals = core.memory.get_recent_signals(limit=5)
    if not signals:
        await message.answer("No signals have been recorded yet.")
        return

    response_text = "<b>Last 5 Recorded Signals:</b>\n\n"
    for s in signals:
        response_text += (
            f"<b>{s['symbol']}</b> - {s['signal_type']} "
            f"({s['timestamp'].strftime('%Y-%m-%d %H:%M')})\n"
            f"<i>Reason: {s['reason']}</i>\n\n"
        )
    await message.answer(response_text)

@dp.message(F.text)
async def handle_chat(message: Message):
    """
    Обработчик текстовых сообщений.
    Передает запрос в ядро для получения ответа от LLM.
    """
    await message.answer("Thinking based on my memory...")
    response = await core.get_chat_response(message.text)
    await message.answer(response)

# --- Жизненный цикл бота ---

async def on_startup(bot: Bot):
    """Выполняется при запуске бота."""
    await set_main_menu(bot)
    logger.info("Bot has started and is polling. The Godfather is listening.")

async def on_shutdown():
    """Выполняется при остановке бота."""
    logger.info("Bot is shutting down...")
    await core.shutdown()
    logger.info("Bot has shut down gracefully.")

async def main():
    """Основная функция для запуска бота."""
    dp.startup.register(on_startup)
    # Используем atexit или другой механизм для graceful shutdown,
    # aiogram 3.x не имеет прямого shutdown-хука в `start_polling`.
    # Для простоты положимся на `finally`
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot polling stopped by user.")
