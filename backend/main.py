# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Импортируем наши будущие модули
from .poet import Poet
from .matrix import generate_insight as generate_insight_from_gene

app = FastAPI(
    title="Digital Sanctuary API",
    description="The gateway to an AI that creates personalized wellness journeys.",
    version="1.0.0"
)

poet = Poet()

class TextIn(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "The sanctuary is silent. Awaiting input."}

@app.post("/generate_insight")
def generate_insight(payload: TextIn):
    if not payload.text:
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")

    try:
        # Шаг 1: Превращаем текст в ген
        gene = poet.text_to_gene(payload.text)

        # Шаг 2: Генерируем инсайт на основе гена
        insight = generate_insight_from_gene(gene)

        # Шаг 3: Конвертируем numpy-типы в стандартные Python-типы перед отправкой.
        # Это нужно, потому что FastAPI/Pydantic по умолчанию не умеют сериализовать numpy-числа.
        if 'gene_used' in insight:
            for key, value in insight['gene_used'].items():
                if hasattr(value, 'item'): # numpy numbers have an .item() method to convert them
                    insight['gene_used'][key] = value.item()

        return insight
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
