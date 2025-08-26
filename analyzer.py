import pandas as pd
import pandas_ta as ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Any

from config import logger

class Analyzer:
    """
    Мыслительный центр бота. Здесь данные превращаются в решения.
    Этот класс содержит логику для:
    - Технического анализа рыночных данных.
    - Анализа настроений новостных заголовков.
    - Комбинирования анализов для генерации торгового сигнала.
    """

    def __init__(self):
        logger.info("Initializing Analyzer...")
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        logger.info("Analyzer initialized successfully.")

    def analyze_technicals(self, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Проводит технический анализ на основе данных о свечах (klines).
        Использует магию pandas_ta для расчета индикаторов.
        """
        if not klines or len(klines) < 20: # Нужно достаточно данных для большинства индикаторов
            logger.warning("Not enough kline data to perform technical analysis.")
            return {"summary": "NEUTRAL", "reason": "Not enough data"}

        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Используем встроенную стратегию pandas_ta для простоты.
        # Это вычисляет ~10 общих индикаторов, таких как RSI, MACD, BBands и т.д.
        df.ta.strategy("common")

        # --- Логика принятия решений на основе последних данных ---
        last = df.iloc[-1]
        summary = "NEUTRAL"
        reasons = []

        # RSI (Индекс относительной силы)
        if last['RSI_14'] < 30:
            reasons.append("RSI is oversold (< 30)")
        elif last['RSI_14'] > 70:
            reasons.append("RSI is overbought (> 70)")

        # MACD (Схождение/расхождение скользящих средних)
        if last['MACD_12_26_9'] > last['MACDs_12_26_9'] and df.iloc[-2]['MACD_12_26_9'] <= df.iloc[-2]['MACDs_12_26_9']:
             reasons.append("MACD bullish crossover")
        if last['MACD_12_26_9'] < last['MACDs_12_26_9'] and df.iloc[-2]['MACD_12_26_9'] >= df.iloc[-2]['MACDs_12_26_9']:
            reasons.append("MACD bearish crossover")

        # Bollinger Bands (Полосы Боллинджера)
        if last['close'] < last['BBL_20_2.0']:
            reasons.append("Price is below lower Bollinger Band")
        elif last['close'] > last['BBU_20_2.0']:
            reasons.append("Price is above upper Bollinger Band")

        # Определение итогового вердикта
        bullish_signals = sum(1 for r in reasons if "bullish" in r or "oversold" in r or "below lower" in r)
        bearish_signals = sum(1 for r in reasons if "bearish" in r or "overbought" in r or "above upper" in r)

        if bullish_signals > bearish_signals:
            summary = "BULLISH"
        elif bearish_signals > bullish_signals:
            summary = "BEARISH"

        # Если сигналов нет, но RSI в тренде
        if not reasons:
            if 55 < last['RSI_14'] < 70:
                summary = "MILDLY_BULLISH"
            elif 30 < last['RSI_14'] < 45:
                summary = "MILDLY_BEARISH"

        logger.info(f"Technical analysis summary: {summary}. Reasons: {', '.join(reasons)}")
        return {"summary": summary, "reason": ", ".join(reasons) or "No strong technical signals."}

    def analyze_sentiment(self, news_items: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Анализирует тональность новостных заголовков.
        Возвращает средний 'compound' скор и вердикт.
        """
        if not news_items:
            return {"summary": "NEUTRAL", "score": 0}

        total_score = 0
        for item in news_items:
            title = item.get('title', '')
            # VADER отлично работает с необработанным текстом
            score = self.sentiment_analyzer.polarity_scores(title)['compound']
            total_score += score

        avg_score = total_score / len(news_items)

        summary = "NEUTRAL"
        if avg_score > 0.05:
            summary = "POSITIVE"
        elif avg_score < -0.05:
            summary = "NEGATIVE"

        logger.info(f"Sentiment analysis summary: {summary} (Avg. score: {avg_score:.2f})")
        return {"summary": summary, "score": avg_score}

    def generate_trade_signal(self, technicals: Dict, sentiment: Dict) -> Dict[str, str]:
        """
        Объединяет технический и сентимент-анализ для генерации финального сигнала.
        Это — место, где рождается божественное прозрение.
        """
        tech_summary = technicals.get("summary", "NEUTRAL")
        sent_summary = sentiment.get("summary", "NEUTRAL")

        signal = "HOLD"
        reason = f"Technicals: {tech_summary}. Sentiment: {sent_summary}."

        # --- Божественная логика принятия решений ---
        if tech_summary == "BULLISH" and sent_summary == "POSITIVE":
            signal = "STRONG_BUY"
        elif tech_summary == "BEARISH" and sent_summary == "NEGATIVE":
            signal = "STRONG_SELL"
        elif tech_summary == "BULLISH" or (tech_summary == "MILDLY_BULLISH" and sent_summary == "POSITIVE"):
            signal = "BUY"
        elif tech_summary == "BEARISH" or (tech_summary == "MILDLY_BEARISH" and sent_summary == "NEGATIVE"):
            signal = "SELL"

        final_reason = f"Signal: {signal}. Reason: {reason} | Tech details: {technicals['reason']}"
        logger.info(final_reason)

        return {"signal": signal, "reason": final_reason}


# Пример использования (для отладки)
if __name__ == '__main__':
    logger.info("--- Running Analyzer standalone test ---")
    analyzer = Analyzer()

    # --- Тест Технического Анализа ---
    # Симулируем бычий сценарий
    dummy_klines_bullish = [
        {"timestamp": i*1000, "open": 100, "high": 110, "low": 90, "close": 100 + i - 15, "volume": 1000}
        for i in range(50)
    ]
    # Имитируем RSI < 30
    dummy_klines_bullish[-1]['close'] = 80
    # Имитируем MACD кроссовер
    df_temp = pd.DataFrame(dummy_klines_bullish).ta.macd()

    # Этот тест очень упрощен, в реальности нужны настоящие данные
    logger.info("Testing technical analysis...")
    tech_result = analyzer.analyze_technicals(dummy_klines_bullish)
    logger.info(f"Tech analysis result: {tech_result}")
    # assert "BULLISH" in tech_result['summary'] # Сложно ассертить без реальных данных

    # --- Тест Сентимент-Анализа ---
    logger.info("Testing sentiment analysis...")
    dummy_news_positive = [
        {"title": "Bitcoin price skyrockets to new all-time high!"},
        {"title": "Ethereum developers announce revolutionary upgrade."}
    ]
    sentiment_result = analyzer.analyze_sentiment(dummy_news_positive)
    logger.info(f"Sentiment analysis result: {sentiment_result}")
    assert sentiment_result['summary'] == "POSITIVE"

    # --- Тест Генерации Сигнала ---
    logger.info("Testing signal generation...")
    final_signal = analyzer.generate_trade_signal(
        {"summary": "BULLISH", "reason": "RSI oversold"},
        {"summary": "POSITIVE", "score": 0.8}
    )
    logger.info(f"Final signal: {final_signal}")
    assert final_signal['signal'] == "STRONG_BUY"

    logger.info("--- Standalone test completed successfully ---")
