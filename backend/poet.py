import spacy
import numpy as np
from spacy.lang.en.stop_words import STOP_WORDS

class Poet:
    """
    Анализирует текст для извлечения его "души" в виде числовых параметров.
    """

    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "Spacy model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )

    def _normalize(self, value, min_val, max_val):
        """Нормализует значение в диапазон от 0 до 1."""
        if max_val == min_val: return 0.5
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def text_to_gene(self, text: str) -> dict:
        """Анализирует текст и возвращает 'ген'."""
        doc = self.nlp(text)

        sentences = list(doc.sents)
        if not sentences: return self._get_default_gene()

        words_per_sentence = [len([t for t in s if t.is_alpha]) for s in sentences]
        avg_sentence_length = np.mean(words_per_sentence) if words_per_sentence else 0

        all_words = [t.lemma_.lower() for t in doc if t.is_alpha and t.lemma_.lower() not in STOP_WORDS]
        if not all_words: return self._get_default_gene()

        unique_words = set(all_words)
        vocabulary_richness = len(unique_words) / len(all_words)

        sentence_length_std = np.std(words_per_sentence) if len(words_per_sentence) > 1 else 0
        rhythm_consistency = 1.0 - self._normalize(sentence_length_std, 0, 15)

        # 'sentiment' is not a standard spacy attribute, we'd need a textblob component for this.
        # For now, we'll simulate it with vector norms.
        aggressiveness = np.mean([t.vector_norm for t in doc if t.has_vector and t.is_alpha])

        gene = {
            "complexity": self._normalize(avg_sentence_length, 5, 30),
            "richness": self._normalize(vocabulary_richness, 0.4, 1.0),
            "rhythm": self._normalize(rhythm_consistency, 0.5, 1.0),
            "sentiment": self._normalize(aggressiveness, 6, 8) # Typical vector norms are in this range
        }

        return gene

    def _get_default_gene(self) -> dict:
        return {"complexity": 0.5, "richness": 0.5, "rhythm": 0.5, "sentiment": 0.5}
