import asyncio
from aiogram import Bot
from core import GodfatherCore
from config import logger, settings

# Список монет, за которыми мы будем неустанно следить.
WATCHLIST = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
# Интервал проверки в секундах. Для реального использования лучше ставить 3600 (1 час) или больше.
# Для демонстрации поставим меньше.
CHECK_INTERVAL_SECONDS = 3600

async def run_monitoring(bot: Bot, core: GodfatherCore):
    """
    Бесконечный цикл, который следит за рынком и отправляет сигналы.
    Это — вечный дозор бота.
    """
    logger.info(f"Starting market monitoring for {WATCHLIST} with interval {CHECK_INTERVAL_SECONDS}s.")
    while True:
        try:
            logger.info("Running scheduled market check...")
            for symbol in WATCHLIST:
                result = await core.process_symbol_for_signal(symbol)

                if "error" in result:
                    logger.error(f"Monitoring error for {symbol}: {result['error']}")
                    continue

                signal_data = result.get('signal', {})
                signal = signal_data.get('signal', "HOLD")

                # --- Отправляем сигнал, только если он не HOLD ---
                if signal != "HOLD":
                    logger.info(f"Significant signal '{signal}' found for {symbol}. Notifying admin.")
                    technicals = result.get('technicals', {})
                    signal_color = "🟢" if "BUY" in signal else "🔴" if "SELL" in signal else "⚪️"

                    message_text = (
                        f"<b>🔔 Proactive Signal Alert 🔔</b>\n"
                        f"--------------------------------------\n"
                        f"<b>{symbol}</b> -> <b>{signal} {signal_color}</b>\n\n"
                        f"<b>Reason:</b>\n"
                        f"<code>{technicals.get('reason', 'N/A')}</code>"
                    )

                    # Отправляем сообщение каждому администратору из списка
                    for admin_id in settings.ADMIN_IDS:
                        await bot.send_message(admin_id, message_text)

            logger.info(f"Scheduled check finished. Sleeping for {CHECK_INTERVAL_SECONDS} seconds.")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"An unexpected error occurred in the monitoring loop: {e}")
            # В случае серьезной ошибки, ждем дольше, чтобы не спамить логами
            await asyncio.sleep(CHECK_INTERVAL_SECONDS * 2)
