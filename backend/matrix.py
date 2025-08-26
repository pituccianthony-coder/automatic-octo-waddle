# backend/matrix.py

import numpy as np
from pprint import pprint

def _generate_sine_market(data_points: int, gene: dict) -> np.ndarray:
    """
    Генерирует синусоидальный рынок. Это — наша "матрица",
    предсказуемая реальность, которую мы пытаемся "взломать".
    Параметры гена влияют на волатильность и тренд рынка.
    """
    # 'aggression' гена определяет волатильность
    volatility = 1 + (gene['aggression'] * 5) # от 1 до 6
    # 'richness' гена определяет долгосрочный тренд
    trend = gene['richness'] * 0.001 # от 0 до 0.001

    x = np.arange(data_points)
    # Синусоида с шумом, волатильностью и трендом
    prices = 100 + np.sin(x * 0.1) * 10 * volatility + np.random.randn(data_points) * 0.5 + x * trend
    return prices

def simulate_market(gene: dict, data_points: int = 500) -> dict:
    """
    Запускает симуляцию торгов на основе гена на сгенерированном рынке.
    """
    prices = _generate_sine_market(data_points, gene)

    initial_capital = 1000.0
    capital = initial_capital
    crypto_held = 0.0

    # --- Логика торговли на основе гена ---
    # 'complexity' определяет размер окна для скользящей средней.
    # Чем сложнее поэма, тем более долгосрочную перспективу "видит" бот.
    short_window = int(5 + gene['complexity'] * 20) # от 5 до 25
    long_window = int(15 + gene['complexity'] * 45) # от 15 до 60

    # Убедимся, что окна не выходят за пределы данных
    if long_window >= data_points:
        return {"error": "Not enough data for the given gene complexity."}

    short_ma = np.convolve(prices, np.ones(short_window), 'valid') / short_window
    long_ma = np.convolve(prices, np.ones(long_window), 'valid') / long_window

    # Начинаем торговлю с момента, когда у нас есть обе скользящие средние
    trade_start_index = long_window - short_window

    for i in range(trade_start_index, len(long_ma)):
        current_price = prices[i + long_window - 1]

        # 'rhythm' определяет порог для принятия решений.
        # Чем ритмичнее стих, тем более четкий сигнал нужен боту.
        crossover_threshold = 0.1 + (1 - gene['rhythm'])

        # Покупаем, если короткая МА пересекает длинную МА снизу вверх
        if short_ma[i] > long_ma[i] and short_ma[i-1] <= long_ma[i-1] and capital > 0:
            if abs(short_ma[i] - long_ma[i]) > crossover_threshold:
                crypto_held = capital / current_price
                capital = 0.0

        # Продаем, если короткая МА пересекает длинную МА сверху вниз
        elif short_ma[i] < long_ma[i] and short_ma[i-1] >= long_ma[i-1] and crypto_held > 0:
            if abs(short_ma[i] - long_ma[i]) > crossover_threshold:
                capital = crypto_held * current_price
                crypto_held = 0.0

    # Продаем все в конце, чтобы посчитать итоговый капитал
    if crypto_held > 0:
        capital = crypto_held * prices[-1]

    profit = capital - initial_capital
    profit_percent = (profit / initial_capital) * 100

    return {
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
        "profit": round(profit, 2),
        "profit_percent": round(profit_percent, 2),
        "gene_used": gene
    }

# --- Демонстрация Работы ---
if __name__ == '__main__':
    print("--- Демонстрация работы симулятора матрицы ---")

    # Ген, который должен быть "хорошим" (высокая сложность, хороший ритм)
    good_gene = {'complexity': 0.8, 'richness': 0.7, 'rhythm': 0.9, 'aggression': 0.4}

    # Ген, который должен быть "плохим" (низкая сложность, плохой ритм)
    bad_gene = {'complexity': 0.1, 'richness': 0.2, 'rhythm': 0.2, 'aggression': 0.8}

    print("\n--- Симуляция с 'хорошим' геном ---")
    good_result = simulate_market(good_gene)
    pprint(good_result)

    print("\n--- Симуляция с 'плохим' геном ---")
    bad_result = simulate_market(bad_gene)
    pprint(bad_result)

    # Ожидаемый результат: хороший ген должен показать лучшую прибыльность
    assert good_result['profit'] > bad_result['profit']
    print("\nТестовые предположения верны. 'Хороший' ген оказался более прибыльным.")
    print("Симулятор матрицы функционален.")
