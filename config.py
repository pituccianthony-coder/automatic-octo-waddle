import os
import logging
from typing import List, Optional
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env в корневой директории
# Это позволяет нам не хранить секреты прямо в коде. Божественно и безопасно.
load_dotenv()

class Settings(BaseSettings):
    """
    Класс для управления настройками проекта.
    Pydantic автоматически читает переменные окружения (с учетом регистра).
    Например, для `bot_token` он будет искать переменную окружения `BOT_TOKEN`.
    """
    # --- Telegram Bot Settings ---
    BOT_TOKEN: str = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # Токен для вашего Telegram-бота
    ADMIN_IDS: List[int] = [123456789]  # Список ID администраторов бота

    # --- Database and Memory Settings ---
    DB_FILE: str = "godfather_bot.db"  # Файл базы данных SQLite
    FAISS_INDEX_PATH: str = "faiss_index.idx"  # Путь для сохранения индекса FAISS

    # --- AI (Ollama) Settings ---
    OLLAMA_MODEL: str = "mistral:7b-instruct-q4_K_M"  # Модель, которую будет использовать Ollama
    OLLAMA_HOST: str = "http://localhost:11434"      # URL для API Ollama

    # --- API Keys for Scrapers ---
    # Оставим пустыми по умолчанию, но бот будет ругаться, если они понадобятся
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None

    # --- Logging Settings ---
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

# --- Инициализация и экспорт настроек ---
# Создаем единственный экземпляр настроек, который будет использоваться во всем проекте.
# Паттерн Singleton в его божественном проявлении.
settings = Settings()

# --- Настройка логирования ---
# Чтобы логи были красивыми и информативными, а не просто криками в пустоту.
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Можно создать специальный логгер для нашего приложения
logger = logging.getLogger("GodfatherBot")
logger.info("Configuration and logging initialized successfully. The God is watching.")

# Пример того, как можно будет использовать конфиг в других файлах:
# from config import settings, logger
# logger.info(f"Bot token loaded: {settings.BOT_TOKEN[:5]}...")
# logger.warning("This is a test warning.")
