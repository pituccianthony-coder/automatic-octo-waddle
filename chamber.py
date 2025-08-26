import asyncio
from pprint import pprint
import random

from core import GodfatherCore
from evolution import create_population, crossover, mutate, generate_fake_klines
from config import logger

class EvolutionChamber:
    """
    Симуляция, в которой торговые стратегии (гены) эволюционируют.
    Это — Колизей для наших цифровых гладиаторов.
    """

    def __init__(self, symbol: str, population_size: int, generations: int, mutation_rate: float):
        self.core = GodfatherCore()
        self.symbol = symbol
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.historical_data = []

    def _prepare_data(self, days: int):
        """Генерирует синтетические исторические данные для бэктестинга."""
        logger.info(f"Generating synthetic historical data for the last {days} days...")
        self.historical_data = generate_fake_klines(days=days)
        if not self.historical_data:
            raise ValueError("Could not generate historical data for backtesting.")
        logger.info(f"Successfully generated {len(self.historical_data)} synthetic klines.")

    async def _calculate_fitness(self, gene: dict) -> float:
        """
        Проводит бэктестинг одного гена на исторических данных и возвращает его "приспособленность".
        Приспособленность = итоговый капитал.
        """
        initial_capital = 1000.0
        capital = initial_capital
        crypto_held = 0.0

        # Мы не можем анализировать самые первые данные, так как у них нет истории
        # для расчета индикаторов. Пропускаем их.
        min_klines_for_analysis = 100 # Безопасное значение

        for i in range(min_klines_for_analysis, len(self.historical_data)):
            # Берем срез данных, как если бы мы видели только прошлое
            current_data_slice = self.historical_data[:i]

            # Получаем сигнал от ядра, отключая запись в память
            result = await self.core.process_symbol_with_gene(
                self.symbol,
                gene,
                store_memory=False
            )

            signal = result.get("signal", {}).get("signal", "HOLD")
            current_price = current_data_slice[-1]['close']

            if "BUY" in signal and capital > 0:
                crypto_held = capital / current_price
                capital = 0.0
            elif "SELL" in signal and crypto_held > 0:
                capital = crypto_held * current_price
                crypto_held = 0.0

        # В конце симуляции, если у нас осталась криптовалюта, продаем ее по последней цене
        if crypto_held > 0:
            capital = crypto_held * self.historical_data[-1]['close']

        return round(capital, 2)

    async def run(self):
        """Запускает полный цикл эволюции."""
        self._prepare_data(days=90) # Генерируем данные за 3 месяца

        population = create_population(self.population_size)

        for gen in range(self.generations):
            logger.info(f"\n--- G E N E R A T I O N {gen + 1}/{self.generations} ---")

            # Оцениваем приспособленность каждого гена
            fitness_scores = await asyncio.gather(*[self._calculate_fitness(gene) for gene in population])

            # Соединяем гены с их результатами
            population_with_fitness = sorted(
                zip(population, fitness_scores),
                key=lambda item: item[1],
                reverse=True
            )

            best_gene = population_with_fitness[0][0]
            best_fitness = population_with_fitness[0][1]

            logger.info(f"Best fitness in generation {gen + 1}: ${best_fitness}")
            logger.info(f"Best gene: {best_gene}")

            # --- Отбор и Размножение ---
            # Выбираем 50% лучших для размножения
            survivor_count = self.population_size // 2
            survivors = [item[0] for item in population_with_fitness[:survivor_count]]

            # Создаем новое поколение
            next_population = survivors # Элитизм: лучшие переходят напрямую

            while len(next_population) < self.population_size:
                parent1, parent2 = random.choices(survivors, k=2)
                child = crossover(parent1, parent2)
                mutated_child = mutate(child, self.mutation_rate)
                next_population.append(mutated_child)

            population = next_population

        logger.info("\n--- Evolution simulation finished! ---")
        await self.core.shutdown()
        return best_gene, best_fitness


async def main():
    chamber = EvolutionChamber(
        symbol='BTC/USDT',
        population_size=10, # Маленькая популяция для быстрой демонстрации
        generations=5,      # Всего 5 поколений
        mutation_rate=0.1
    )
    await chamber.run()

if __name__ == "__main__":
    asyncio.run(main())
