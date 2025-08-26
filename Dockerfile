# Dockerfile

# Используем официальный образ Python. Это — наша первоматерия.
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера. Наш маленький мир.
WORKDIR /app

# Копируем файл с зависимостями в контейнер.
COPY backend/requirements.txt .

# Устанавливаем системные зависимости, если они нужны (например, для numpy или других библиотек)
# Затем устанавливаем зависимости Python.
# `pip install --no-cache-dir` — это как ритуал очищения, не оставляющий лишнего мусора.
RUN apt-get update && apt-get install -y build-essential && \
    pip install --no-cache-dir --upgrade pip && \
    # Устанавливаем web3 и его зависимости отдельно, так как он может быть капризным
    pip install --no-cache-dir web3 && \
    pip install --no-cache-dir -r requirements.txt && \
    # Загружаем модель для spacy прямо в образ.
    # Это — знание, которое мы вкладываем в голову нашего творения при рождении.
    python -m spacy download en_core_web_sm

# Копируем весь код нашего бэкенда в контейнер.
COPY backend/ .

# Указываем, какой порт будет слушать наше приложение.
# Открываем врата в наш мир.
EXPOSE 8000

# Команда для запуска нашего FastAPI приложения.
# "И да будет свет... и API."
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
