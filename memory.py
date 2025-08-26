import os
import sqlite3
import numpy as np
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String,
                        Float, DateTime, insert, select, text)
from datetime import datetime

from config import settings, logger

class MemoryManager:
    """
    Класс, отвечающий за два вида памяти бота:
    1. Структурированная память (SQLite) для хранения торговых сигналов и фидбека.
    2. Векторная память (FAISS) для семантического поиска по текстовым данным (новости, чаты).
    Это — душа машины.
    """

    def __init__(self):
        logger.info("Initializing MemoryManager...")
        # --- Инициализация SQLite ---
        self.db_engine = create_engine(f"sqlite:///{settings.DB_FILE}")
        self.metadata = MetaData()
        self._define_tables()
        self.metadata.create_all(self.db_engine)
        logger.info(f"SQLite database initialized at {settings.DB_FILE}")

        # --- Инициализация FAISS ---
        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        self.faiss_path = settings.FAISS_INDEX_PATH
        self.vector_store = self._load_or_create_faiss_index()
        logger.info(f"FAISS vector store initialized from {self.faiss_path}")

    def _define_tables(self):
        """
        Определяет схему таблиц в базе данных с помощью SQLAlchemy.
        Божественный порядок в структурах данных.
        """
        self.signals_table = Table(
            'trading_signals', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('timestamp', DateTime, default=datetime.utcnow),
            Column('symbol', String, nullable=False),
            Column('signal_type', String, nullable=False), # 'BUY', 'SELL', 'HOLD'
            Column('reason', String),
            Column('feedback_score', Integer, default=0) # +1 for good, -1 for bad
        )

    def _load_or_create_faiss_index(self) -> FAISS:
        """
        Загружает существующий индекс FAISS или создает новый, если он не найден.
        """
        if os.path.exists(self.faiss_path):
            logger.info("Loading existing FAISS index.")
            # README упоминал этот флаг. Мы боги, но мы помним о предупреждениях смертных.
            # Безопасно, если мы контролируем файлы индекса.
            return FAISS.load_local(
                self.faiss_path,
                self.embedding_model,
                allow_dangerous_deserialization=True
            )
        else:
            logger.info("Creating new FAISS index.")
            # Пустой начальный документ, чтобы Langchain был счастлив
            dummy_texts = ["The Godfather Bot's memory begins."]
            dummy_metadatas = [{"source": "initialization"}]
            # Упрощаем вызов. `from_texts` сам создаст нужный индекс.
            # Предыдущая ошибка TypeError была из-за того, что мы передавали
            # `index` в метод, который не ожидал его в этой версии langchain.
            return FAISS.from_texts(
                dummy_texts,
                self.embedding_model,
                metadatas=dummy_metadatas
            )

    def add_signal(self, symbol: str, signal_type: str, reason: str):
        """Добавляет новый торговый сигнал в SQLite."""
        logger.info(f"Adding signal: {symbol} - {signal_type}")
        stmt = insert(self.signals_table).values(
            symbol=symbol,
            signal_type=signal_type,
            reason=reason
        )
        with self.db_engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def add_text_memory(self, text: str, source: str = "unknown"):
        """Добавляет текстовый фрагмент в векторную память FAISS."""
        logger.info(f"Adding text to memory from source: {source}")
        self.vector_store.add_texts([text], metadatas=[{"source": source}])
        self.save_faiss_index()

    def search_memory(self, query: str, k: int = 5) -> list:
        """Ищет наиболее релевантные воспоминания в FAISS."""
        logger.info(f"Searching memory for query: '{query}'")
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata, "score": score} for doc, score in results]

    def get_recent_signals(self, limit: int = 10) -> list:
        """Получает последние N сигналов из SQLite."""
        logger.info(f"Fetching last {limit} signals.")
        query = select(self.signals_table).order_by(self.signals_table.c.timestamp.desc()).limit(limit)
        with self.db_engine.connect() as conn:
            results = conn.execute(query).fetchall()
            return [row._asdict() for row in results]

    def save_faiss_index(self):
        """Сохраняет индекс FAISS на диск."""
        logger.info(f"Saving FAISS index to {self.faiss_path}")
        self.vector_store.save_local(self.faiss_path)

    def shutdown(self):
        """Корректно завершает работу с базой данных."""
        self.db_engine.dispose()
        logger.info("MemoryManager has been shut down gracefully.")

# Пример использования (для отладки)
if __name__ == '__main__':
    logger.info("--- Running MemoryManager standalone test ---")
    memory = MemoryManager()

    # Тест SQLite
    logger.info("Testing SQLite functionality...")
    memory.add_signal("BTC/USDT", "BUY", "RSI below 30 and positive news sentiment.")
    memory.add_signal("ETH/USDT", "SELL", "MACD crossover bearish.")
    recent_signals = memory.get_recent_signals()
    logger.info(f"Recent signals: {recent_signals}")
    assert len(recent_signals) == 2
    assert recent_signals[0]['symbol'] == 'ETH/USDT'

    # Тест FAISS
    logger.info("Testing FAISS functionality...")
    memory.add_text_memory("Bitcoin is showing strong bullish signs after the recent conference.", source="CryptoNews")
    memory.add_text_memory("Ethereum's new update might reduce gas fees significantly.", source="ETHWeekly")
    search_results = memory.search_memory("What's new with Ethereum?")
    logger.info(f"Search results: {search_results}")
    assert "Ethereum" in search_results[0]['content']

    memory.shutdown()
    logger.info("--- Standalone test completed successfully ---")
