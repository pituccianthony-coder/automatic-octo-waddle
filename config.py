import os
import logging
from typing import List, Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env в корневой директории
load_dotenv()

class Settings(BaseSettings):
    """
    Класс для управления настройками проекта GODFATHER Bot.
    """
    # --- Telegram Bot Settings ---
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
    ADMIN_IDS: List[int] = [123456789]

    # --- Database and Memory Settings ---
    DB_FILE: str = "godfather_bot.db"
    FAISS_INDEX_PATH: str = "faiss_index.idx"

    # --- AI (Ollama) Settings ---
    OLLAMA_MODEL: str = "mistral:7b"
    OLLAMA_HOST: str = "http://localhost:11434"

    # --- API Keys for Scrapers ---
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None

    # --- Logging Settings ---
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

# --- Инициализация и экспорт настроек ---
settings = Settings()

# --- Настройка логирования ---
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("GodfatherBot")
logger.info("Configuration and logging for GODFATHER Bot initialized.")
