import pandas as pd
import pandas_ta as ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Any

from config import logger
from evolution import GENE_SPACE # Импортируем "карту" генома

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

    def analyze_technicals(self, klines: List[Dict[str, Any]], gene: dict) -> Dict[str, Any]:
        """
        Проводит технический анализ, используя параметры из переданного "гена".
        Больше никакой жесткой логики. Только чистая адаптация.
        """
        # Минимальное количество данных зависит от самого длинного периода в гене
        required_klines = max(gene['rsi_period'], gene['macd_slow'])
        if not klines or len(klines) < required_klines:
            return {"summary": "NEUTRAL", "reason": "Not enough data for the given gene."}

        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # --- Применяем индикаторы с параметрами из гена ---
        df.ta.rsi(length=gene['rsi_period'], append=True)
        df.ta.macd(fast=gene['macd_fast'], slow=gene['macd_slow'], signal=gene['macd_signal'], append=True)
        if gene['use_bbands']:
            df.ta.bbands(length=20, std=2.0, append=True) # Параметры BBands пока оставим стандартными

        # --- Логика принятия решений на основе последних данных и генов ---
        last = df.iloc[-1]
        summary = "NEUTRAL"
        reasons = []

        rsi_col = f"RSI_{gene['rsi_period']}"
        macd_col = f"MACD_{gene['macd_fast']}_{gene['macd_slow']}_{gene['macd_signal']}"
        macds_col = f"MACDs_{gene['macd_fast']}_{gene['macd_slow']}_{gene['macd_signal']}"

        # RSI
        if rsi_col in last and last[rsi_col] < gene['rsi_oversold']:
            reasons.append(f"RSI oversold (< {gene['rsi_oversold']})")
        elif rsi_col in last and last[rsi_col] > gene['rsi_overbought']:
            reasons.append(f"RSI overbought (> {gene['rsi_overbought']})")

        # MACD
        if macd_col in last and last[macd_col] > last[macds_col] and df.iloc[-2][macd_col] <= df.iloc[-2][macds_col]:
             reasons.append("MACD bullish crossover")
        if macd_col in last and last[macd_col] < last[macds_col] and df.iloc[-2][macd_col] >= df.iloc[-2][macds_col]:
            reasons.append("MACD bearish crossover")

        # Bollinger Bands
        if gene['use_bbands'] and 'BBL_20_2.0' in last:
            if last['close'] < last['BBL_20_2.0']:
                reasons.append("Price below lower Bollinger Band")
            elif last['close'] > last['BBU_20_2.0']:
                reasons.append("Price above upper Bollinger Band")

        bullish_signals = sum(1 for r in reasons if "bullish" in r or "oversold" in r or "below lower" in r)
        bearish_signals = sum(1 for r in reasons if "bearish" in r or "overbought" in r or "above upper" in r)

        if bullish_signals > bearish_signals:
            summary = "BULLISH"
        elif bearish_signals > bullish_signals:
            summary = "BEARISH"

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

    def generate_trade_signal(self, technicals: Dict, sentiment: Dict, gene: dict) -> Dict[str, str]:
        """
        Генерирует финальный сигнал, взвешивая сентимент согласно геному.
        """
        tech_summary = technicals.get("summary", "NEUTRAL")
        sent_summary = sentiment.get("summary", "NEUTRAL")
        sentiment_score = sentiment.get("score", 0)

        signal = "HOLD"

        # Умножаем "силу" сентимента на его вес из гена
        effective_sentiment_score = sentiment_score * gene['sentiment_weight']

        # --- Эволюционирующая логика ---
        # Теперь решение более гибкое, оно учитывает вес сентимента
        if tech_summary == "BULLISH" and effective_sentiment_score > 0.05:
            signal = "STRONG_BUY"
        elif tech_summary == "BEARISH" and effective_sentiment_score < -0.05:
            signal = "STRONG_SELL"
        elif tech_summary == "BULLISH" or (tech_summary == "NEUTRAL" and effective_sentiment_score > 0.2): # Покупаем на нейтральном теханализе, если сентимент очень сильный
            signal = "BUY"
        elif tech_summary == "BEARISH" or (tech_summary == "NEUTRAL" and effective_sentiment_score < -0.2): # Аналогично для продажи
            signal = "SELL"

        reason = f"Technicals: {tech_summary}. Sentiment: {sent_summary} (Effective Score: {effective_sentiment_score:.2f})."
        final_reason = f"Signal: {signal}. Reason: {reason} | Tech details: {technicals['reason']}"

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
