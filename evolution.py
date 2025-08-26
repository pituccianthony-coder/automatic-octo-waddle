import random
import json
from pprint import pprint
from datetime import datetime, timedelta
from config import logger

# --- Определение Генома Стратегии ---
# Это "ДНК" нашего трейдера. Каждый ген - это параметр для анализатора.
# Мы определяем разумные диапазоны для случайной генерации.
GENE_SPACE = {
    # Параметры для RSI
    "rsi_period": {"type": "int", "min": 7, "max": 21},
    "rsi_oversold": {"type": "int", "min": 20, "max": 35},
    "rsi_overbought": {"type": "int", "min": 65, "max": 80},
    # Параметры для MACD
    "macd_fast": {"type": "int", "min": 8, "max": 16},
    "macd_slow": {"type": "int", "min": 18, "max": 30},
    "macd_signal": {"type": "int", "min": 7, "max": 11},
    # Вес, который придается анализу настроений
    "sentiment_weight": {"type": "float", "min": 0.1, "max": 1.0},
    # Использовать ли сигналы по полосам Боллинджера
    "use_bbands": {"type": "bool"}
}

def create_random_gene() -> dict:
    """Создает один случайный 'ген' (торговую стратегию)."""
    gene = {}
    for key, properties in GENE_SPACE.items():
        if properties["type"] == "int":
            gene[key] = random.randint(properties["min"], properties["max"])
        elif properties["type"] == "float":
            gene[key] = round(random.uniform(properties["min"], properties["max"]), 2)
        elif properties["type"] == "bool":
            gene[key] = random.choice([True, False])
    return gene

def create_population(size: int) -> list[dict]:
    """Создает популяцию случайных генов."""
    return [create_random_gene() for _ in range(size)]

# --- Эволюционные Механизмы ---

def crossover(parent1: dict, parent2: dict) -> dict:
    """
    Скрещивание двух родительских генов для создания потомка.
    Имитирует генетическую рекомбинацию.
    """
    child = {}
    for key in GENE_SPACE:
        # Случайно выбираем, ген какого родителя унаследует потомок
        child[key] = random.choice([parent1[key], parent2[key]])
    return child

def mutate(gene: dict, mutation_rate: float) -> dict:
    """
    Случайно мутирует гены в геноме с заданной вероятностью.
    Это вносит новые "идеи" в популяцию.
    """
    mutated_gene = gene.copy()
    for key, properties in GENE_SPACE.items():
        if random.random() < mutation_rate:
            # Если ген мутирует, генерируем для него новое случайное значение
            if properties["type"] == "int":
                mutated_gene[key] = random.randint(properties["min"], properties["max"])
            elif properties["type"] == "float":
                mutated_gene[key] = round(random.uniform(properties["min"], properties["max"]), 2)
            elif properties["type"] == "bool":
                mutated_gene[key] = not mutated_gene[key] # Инвертируем bool
    return mutated_gene


# --- Генератор Синтетических Данных ---
def generate_fake_klines(days: int, timeframe_hours: int = 1) -> list[dict]:
    """
    Создает процедурно-генерируемую историю цен.
    Использует случайное блуждание с моментумом для более "реалистичного" вида.
    """
    logger.info(f"Generating {days} days of fake historical kline data.")
    klines = []
    price = 10000.0  # Начальная цена
    momentum = 0
    start_time = datetime.utcnow() - timedelta(days=days)

    for i in range(days * 24 // timeframe_hours):
        # Добавляем случайное изменение + небольшой моментум
        change = random.uniform(-0.01, 0.01) + momentum
        price *= (1 + change)

        # Моментум тоже "блуждает"
        momentum += random.uniform(-0.001, 0.001)
        momentum *= 0.95 # Затухание моментума

        # Ограничиваем моментум, чтобы цена не улетала в космос
        momentum = max(min(momentum, 0.01), -0.01)

        # Создаем свечу
        open_price = price * random.uniform(0.99, 1.01)
        high_price = max(price, open_price) * random.uniform(1.0, 1.02)
        low_price = min(price, open_price) * random.uniform(0.98, 1.0)
        volume = random.uniform(100, 1000)

        timestamp = int((start_time + timedelta(hours=i * timeframe_hours)).timestamp() * 1000)

        klines.append({
            "timestamp": timestamp,
            "open": open_price, "high": high_price, "low": low_price, "close": price, "volume": volume
        })

    return klines


# --- Демонстрация Работы ---
if __name__ == '__main__':
    # Добавляем импорт логгера для генератора
    from config import logger

    print("--- Демонстрация работы эволюционного ядра ---")

    # 1. Создаем популяцию
    population_size = 5
    population = create_population(population_size)
    print(f"\n1. Создана начальная популяция из {population_size} генов:")
    pprint(population)

    # 2. Выбираем двух родителей
    parent_a = population[0]
    parent_b = population[1]
    print("\n2. Выбраны два родителя для скрещивания:")
    print("   Родитель A:", json.dumps(parent_a))
    print("   Родитель B:", json.dumps(parent_b))

    # 3. Производим скрещивание
    child_c = crossover(parent_a, parent_b)
    print("\n3. Создан потомок путем скрещивания:")
    print("   Потомок C:", json.dumps(child_c))

    # 4. Производим мутацию
    mutation_chance = 0.5 # Высокий шанс для демонстрации
    mutated_child_c = mutate(child_c, mutation_chance)
    print(f"\n4. Потомок мутировал с вероятностью {mutation_chance * 100}%:")
    print("   Мутировавший потомок:", json.dumps(mutated_child_c))

    # Сравниваем, что изменилось
    changes = {k: (child_c[k], mutated_child_c[k]) for k in child_c if child_c[k] != mutated_child_c[k]}
    if changes:
        print("   Обнаружены мутации в генах:")
        pprint(changes)
    else:
        print("   Мутаций не произошло.")

    print("\n--- Эволюционное ядро функционально ---")
