# backend/config.py

import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения. Секреты должны быть в секрете.
load_dotenv()

# --- Настройка логирования ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Создаем логгер для нашего приложения
logger = logging.getLogger("EchoVoid")
logger.info("Logging configured. The void is watching.")

# --- Переменные окружения для Web3 ---
ETHEREUM_PROVIDER_URL = os.getenv("ETHEREUM_PROVIDER_URL", "http://127.0.0.1:8545")
ECHO_DAO_CONTRACT_ADDRESS = os.getenv("ECHO_DAO_CONTRACT_ADDRESS")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY") # // Опасно! Но боги не боятся опасностей.
