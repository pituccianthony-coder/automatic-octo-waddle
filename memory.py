import os
import faiss
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from sqlalchemy import (create_engine, MetaData, Table, Column, Integer, String,
                        Float, DateTime, insert, select)
from datetime import datetime

from config import settings, logger

class MemoryManager:
    """
    Класс, отвечающий за два вида памяти бота:
    1. Структурированная память (SQLite) для хранения торговых сигналов и фидбека.
    2. Векторная память (FAISS) для семантического поиска по текстовым данным.
    """

    def __init__(self):
        logger.info("Initializing MemoryManager...")
        self.db_engine = create_engine(f"sqlite:///{settings.DB_FILE}")
        self.metadata = MetaData()
        self._define_tables()
        self.metadata.create_all(self.db_engine)
        logger.info(f"SQLite database initialized at {settings.DB_FILE}")

        self.embedding_model = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
        self.faiss_path = settings.FAISS_INDEX_PATH
        self.vector_store = self._load_or_create_faiss_index()
        logger.info(f"FAISS vector store initialized from {self.faiss_path}")

    def _define_tables(self):
        self.signals_table = Table(
            'trading_signals', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('timestamp', DateTime, default=datetime.utcnow),
            Column('symbol', String, nullable=False),
            Column('signal_type', String, nullable=False),
            Column('reason', String),
            Column('feedback_score', Integer, default=0)
        )

    def _load_or_create_faiss_index(self) -> FAISS:
        if os.path.exists(self.faiss_path):
            return FAISS.load_local(
                self.faiss_path,
                self.embedding_model,
                allow_dangerous_deserialization=True
            )
        else:
            dummy_texts = ["The Godfather Bot's memory begins."]
            dummy_metadatas = [{"source": "initialization"}]
            return FAISS.from_texts(
                dummy_texts,
                self.embedding_model,
                metadatas=dummy_metadatas
            )

    def add_signal(self, symbol: str, signal_type: str, reason: str):
        stmt = insert(self.signals_table).values(
            symbol=symbol,
            signal_type=signal_type,
            reason=reason
        )
        with self.db_engine.connect() as conn:
            conn.execute(stmt)
            conn.commit()

    def add_text_memory(self, text: str, source: str = "unknown"):
        self.vector_store.add_texts([text], metadatas=[{"source": source}])
        self.save_faiss_index()

    def search_memory(self, query: str, k: int = 5) -> list:
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return [{"content": doc.page_content, "metadata": doc.metadata, "score": score} for doc, score in results]

    def get_recent_signals(self, limit: int = 10) -> list:
        query = select(self.signals_table).order_by(self.signals_table.c.timestamp.desc()).limit(limit)
        with self.db_engine.connect() as conn:
            results = conn.execute(query).fetchall()
            return [row._asdict() for row in results]

    def save_faiss_index(self):
        self.vector_store.save_local(self.faiss_path)

    def shutdown(self):
        self.db_engine.dispose()
        logger.info("MemoryManager has been shut down gracefully.")
