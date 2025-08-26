import pandas as pd
import ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict, Any

from config import logger

class Analyzer:
    """
    Мыслительный центр бота. Здесь данные превращаются в решения.
    """

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def analyze_technicals(self, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not klines or len(klines) < 26: # MACD needs at least 26 periods
            return {"summary": "NEUTRAL", "reason": "Not enough data"}

        df = pd.DataFrame(klines)

        # --- Переписываем логику на библиотеку `ta` ---
        # Она не расширяет pandas, а работает с сериями напрямую.
        df['rsi'] = ta.momentum.rsi(df['close'])
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        last = df.iloc[-1]
        prev = df.iloc[-2]
        summary = "NEUTRAL"
        reasons = []

        if last['rsi'] < 30:
            reasons.append("RSI is oversold (< 30)")
        elif last['rsi'] > 70:
            reasons.append("RSI is overbought (> 70)")

        if last['macd'] > last['macd_signal'] and prev['macd'] <= prev['macd_signal']:
             reasons.append("MACD bullish crossover")
        if last['macd'] < last['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            reasons.append("MACD bearish crossover")

        bullish_signals = sum(1 for r in reasons if "bullish" in r or "oversold" in r)
        bearish_signals = sum(1 for r in reasons if "bearish" in r or "overbought" in r)

        if bullish_signals > bearish_signals:
            summary = "BULLISH"
        elif bearish_signals > bullish_signals:
            summary = "BEARISH"

        return {"summary": summary, "reason": ", ".join(reasons) or "No strong signals."}

    def analyze_sentiment_from_text(self, text: str) -> Dict[str, Any]:
        """Анализирует тональность произвольного текста."""
        score = self.sentiment_analyzer.polarity_scores(text)['compound']
        summary = "NEUTRAL"
        if score > 0.05:
            summary = "POSITIVE"
        elif score < -0.05:
            summary = "NEGATIVE"
        return {"summary": summary, "score": score}

    def generate_trade_signal(self, technicals: Dict, sentiment: Dict) -> Dict[str, str]:
        tech_summary = technicals.get("summary", "NEUTRAL")
        sent_summary = sentiment.get("summary", "NEUTRAL")

        signal = "HOLD"
        if tech_summary == "BULLISH" and sent_summary != "NEGATIVE":
            signal = "BUY"
        elif tech_summary == "BEARISH" and sent_summary != "POSITIVE":
            signal = "SELL"

        reason = f"Technicals: {tech_summary}. Sentiment: {sent_summary}."
        final_reason = f"Signal: {signal}. Reason: {reason} | Tech details: {technicals['reason']}"

        return {"signal": signal, "reason": final_reason}
