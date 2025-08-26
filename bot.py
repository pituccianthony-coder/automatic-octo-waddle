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
# Объекты будут созданы в main(), чтобы избежать проблем при импорте
# и сделать код более чистым и предсказуемым.
dp = Dispatcher()
core = GodfatherCore()


async def set_main_menu(bot: Bot):
    main_menu_commands = [
        BotCommand(command="/analyze", description="Анализ символа (напр. /analyze BTC/USDT)"),
        BotCommand(command="/latest_signals", description="Показать последние 5 сигналов"),
        BotCommand(command="/help", description="Справка по боту"),
    ]
    await bot.set_my_commands(main_menu_commands)

# --- Обработчики команд ---

# Мы не можем использовать декораторы dp, если dp создается в main.
# Вместо этого мы будем регистрировать хэндлеры прямо в main.
async def handle_start(message: Message):
    await message.answer(
        "<b>The Godfather Bot at your service.</b>\n\n"
        "I observe, I analyze, I report. Use /help to see my commands."
    )

async def handle_help(message: Message):
    await message.answer(
        "<b>Commands:</b>\n\n"
        "<code>/analyze [SYMBOL]</code> - Full analysis for a trading pair (e.g., BTC/USDT).\n\n"
        "<code>/latest_signals</code> - Shows the last 5 non-HOLD signals.\n\n"
        "Simply chat with me to get AI-powered responses."
    )

async def handle_analyze(message: Message, bot: Bot):
    symbol = message.text.split()[1] if len(message.text.split()) > 1 else None
    if not symbol:
        await message.answer("Please specify a symbol. Usage: <code>/analyze BTC/USDT</code>")
        return

    symbol = symbol.upper()
    processing_message = await message.answer(f"Submitting {symbol} to the oracle... 🔮")

    result = await core.process_symbol_for_signal(symbol)

    if "error" in result:
        await bot.edit_message_text(f"<b>Analysis failed:</b> {result['error']}", processing_message.chat.id, processing_message.message_id)
        return

    signal = result.get('signal', {})
    technicals = result.get('technicals', {})
    signal_color = "🟢" if "BUY" in signal.get('signal', '') else "🔴" if "SELL" in signal.get('signal', '') else "⚪️"

    response_text = (
        f"<b>Analysis for {result.get('symbol', 'N/A')}</b>\n"
        f"--------------------------------------\n"
        f"<b>Signal: {signal.get('signal', 'N/A')} {signal_color}</b>\n\n"
        f"<b><u>Technical Summary:</u></b>\n"
        f"<i>{technicals.get('summary', 'N/A')}</i>\n"
        f"<code>{technicals.get('reason', 'No specific signals.')}</code>\n\n"
        f"<b><u>Full Reason:</u></b>\n"
        f"<i>{signal.get('reason', 'N/A')}</i>"
    )
    await bot.edit_message_text(response_text, chat_id=processing_message.chat.id, message_id=processing_message.message_id)

async def handle_latest_signals(message: Message):
    signals = core.memory.get_recent_signals(limit=5)
    if not signals:
        await message.answer("No signals have been recorded in memory yet.")
        return

    response_parts = ["<b>Last 5 Recorded Signals:</b>\n--------------------------------------"]
    for s in signals:
        signal_color = "🟢" if "BUY" in s['signal_type'] else "🔴" if "SELL" in s['signal_type'] else "⚪️"
        part = (
            f"<b>{s['symbol']} - {s['signal_type']} {signal_color}</b>\n"
            f"<i>{s['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}</i>\n"
            f"<code>{s['reason']}</code>"
        )
        response_parts.append(part)

    response_text = "\n\n".join(response_parts)
    await message.answer(response_text)

async def handle_chat(message: Message):
    response = await core.get_chat_response(message.text, message.from_user.id)
    await message.answer(response)

# --- Жизненный цикл бота ---

async def main():
    # Инициализируем все здесь, а не в глобальной области видимости
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Регистрируем хэндлеры
    dp.startup.register(set_main_menu)
    dp.message.register(handle_start, Command("start"))
    dp.message.register(handle_help, Command("help"))
    # Используем лямбду, чтобы передать bot в хэндлер
    dp.message.register(lambda msg: handle_analyze(msg, bot), Command("analyze"))
    dp.message.register(handle_latest_signals, Command("latest_signals"))
    dp.message.register(handle_chat, F.text)

    # Управляем жизненным циклом ядра вручную
    try:
        logger.info("The Godfather is awakening...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await core.shutdown()
        logger.info("The Godfather has gone to sleep.")

if __name__ == "__main__":
    asyncio.run(main())
