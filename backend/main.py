# backend/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .poet import Poet
from .matrix import simulate_market

# --- Инициализация ---
# "Собираем Мстителей": создаем экземпляры наших модулей.
app = FastAPI(
    title="EchoVoid API",
    description="An interface to a reality-hacking, poetry-driven, decentralized autonomous artist.",
    version="0.0.1-alpha"
)
poet = Poet()

# --- Модели данных для API ---
class TextInput(BaseModel):
    text: str

class SimulationOutput(BaseModel):
    initial_capital: float
    final_capital: float
    profit: float
    profit_percent: float
    gene_used: dict


# --- Эндпоинты API ---

@app.get("/")
async def root():
    return {"message": "The void echoes back. Submit your poetry to /generate_from_text."}

@app.post("/generate_from_text", response_model=SimulationOutput)
async def generate_from_text(payload: TextInput):
    """
    Главный эндпоинт. Принимает текст, генерирует ген, запускает симуляцию и возвращает результат.
    // Это портал, где искусство становится деньгами (пока что симулированными).
    """
    if not payload.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        # Шаг 1: Превращаем текст в ген
        gene = poet.text_to_gene(payload.text)

        # Шаг 2: Запускаем симуляцию с этим геном
        simulation_result = simulate_market(gene)

        return simulation_result
    except Exception as e:
        # // Если матрица сопротивляется, мы должны хотя бы знать, почему.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
