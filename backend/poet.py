# backend/poet.py

import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import numpy as np

class Poet:
    """
    Этот модуль — поэт-алхимик. Он читает текст и преобразует его
    душу, ритм и сложность в "ген" — набор числовых параметров,
    которые будут управлять поведением торгового симулятора.
    // По сути, мы заставляем машину торговать на основе вайбов Шекспира.
    // Что может пойти не так?
    """

    def __init__(self):
        # Загружаем модель spacy. Если она не найдена, пользователь должен
        # скачать ее командой: python -m spacy download en_core_web_sm
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Spacy model 'en_core_web_sm' not found.")
            print("Please run: python -m spacy download en_core_web_sm")
            raise

    def _normalize(self, value, min_val, max_val):
        """Нормализует значение в диапазон от 0 до 1."""
        # Убедимся, что не делим на ноль и не выходим за границы
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def text_to_gene(self, text: str) -> dict:
        """
        Главный метод. Анализирует текст и возвращает "ген".
        """
        doc = self.nlp(text)

        # --- Извлечение метрик ---

        # 1. Сложность (средняя длина предложения)
        sentences = list(doc.sents)
        if not sentences:
            return self._get_default_gene()

        words_per_sentence = [len([token for token in sent if token.is_alpha]) for sent in sentences]
        avg_sentence_length = np.mean(words_per_sentence) if words_per_sentence else 0

        # 2. Богатство словаря (отношение уникальных слов к общему числу)
        all_words = [token.lemma_.lower() for token in doc if token.is_alpha and token.lemma_.lower() not in STOP_WORDS]
        if not all_words:
            return self._get_default_gene()

        unique_words = set(all_words)
        vocabulary_richness = len(unique_words) / len(all_words)

        # 3. Ритм (стандартное отклонение длины предложений)
        # Низкое отклонение = более стабильный ритм. Мы инвертируем это значение.
        sentence_length_std = np.std(words_per_sentence) if len(words_per_sentence) > 1 else 0
        rhythm_consistency = 1.0 - self._normalize(sentence_length_std, 0, 15) # 15 - примерный максимум

        # 4. "Агрессивность" (количество "сильных" прилагательных и глаголов)
        # Это очень упрощенная метрика, но она добавит интересный параметр.
        strong_words = [token for token in doc if token.pos_ in ["ADJ", "VERB"] and token.has_vector and token.vector_norm > 7.5]
        aggressiveness = len(strong_words) / len(all_words)

        # --- Нормализация и создание гена ---
        gene = {
            "complexity": self._normalize(avg_sentence_length, 5, 30), # от 5 до 30 слов
            "richness": self._normalize(vocabulary_richness, 0.4, 1.0),
            "rhythm": self._normalize(rhythm_consistency, 0.5, 1.0),
            "aggression": self._normalize(aggressiveness, 0, 0.1)
        }

        return gene

    def _get_default_gene(self) -> dict:
        """Возвращает ген по умолчанию, если текст пустой или неанализируемый."""
        return {
            "complexity": 0.5,
            "richness": 0.5,
            "rhythm": 0.5,
            "aggression": 0.5
        }

# --- Демонстрация Работы ---
if __name__ == '__main__':
    poet = Poet()

    poem = """
    Tyger Tyger, burning bright,
    In the forests of the night;
    What immortal hand or eye,
    Could frame thy fearful symmetry?
    """

    prose = """
    The stock market is a complex system influenced by a myriad of factors.
    Economic indicators, geopolitical events, and investor sentiment all play a crucial role.
    Predicting its movements with consistent accuracy remains a significant challenge,
    one that requires sophisticated models and a deep understanding of market dynamics.
    """

    print("--- Анализ Поэзии (Уильям Блейк) ---")
    poem_gene = poet.text_to_gene(poem)
    pprint(poem_gene)

    print("\n--- Анализ Прозы (Финансовый Текст) ---")
    prose_gene = poet.text_to_gene(prose)
    pprint(prose_gene)

    # Ожидаемый результат:
    # Поэма будет иметь более высокий 'rhythm' и 'richness'.
    # Проза будет иметь более высокую 'complexity'.
    assert prose_gene['complexity'] > poem_gene['complexity']
    assert poem_gene['rhythm'] > prose_gene['rhythm']
    print("\nТестовые предположения верны. Модуль работает, как задумано.")
