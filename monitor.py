import logging
import sqlite3
import threading
import time

import pandas as pd
import plotly.graph_objects as go
import requests
import socketio
import streamlit as st
import uvicorn
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import DB_FILE, OLLAMA_MODEL

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Godfather Bot Monitor")
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app.mount("/socket.io", socketio.ASGIApp(sio))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Helper ---
def get_db_connection():
    """Creates and returns a new database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- WebSocket Events ---
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    await sio.emit('status', {'message': 'Connected to Godfather Dashboard'})

# --- API Endpoints ---
@app.post("/dashboard/chat")
async def chat_with_model(message: str = Form(...)):
    """Endpoint for the dashboard to chat with the Ollama model."""
    try:
        # The service name is 'ollama' in docker-compose
        ollama_url = "http://ollama:11434/api/generate"
        payload = {"model": OLLAMA_MODEL, "prompt": message, "stream": False}
        response = requests.post(ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        answer = response.json().get("response", "[No response from model]")
    except Exception as e:
        logger.error(f"Chat with model error: {e}")
        answer = f"[Error communicating with model: {e}]"
    
    # Emit response to all connected dashboard clients
    await sio.emit('chat_response', {'answer': answer})
    return JSONResponse(content={"answer": answer})

@app.get("/signals")
def get_signals():
    """Endpoint to get the last 10 signals from the database."""
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM memory ORDER BY id DESC LIMIT 10", conn)
        conn.close()
        return JSONResponse(content={"signals": df.to_dict(orient='records')})
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/status")
def get_status():
    """Endpoint to get bot status (signal counts)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Fixed: &gt; changed to >
        cursor.execute("SELECT COUNT(*) FROM memory WHERE timestamp > datetime('now', '-1 hour')")
        recent = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM memory")
        total = cursor.fetchone()[0]
        conn.close()
        return {"recent_signals": recent, "total_signals": total}
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- Main Execution ---
if __name__ == "__main__":
    # In this setup, you would run this file with `python monitor.py`
    # and then navigate to your Streamlit URL (e.g., http://localhost:8501)
    # The Streamlit app is defined in a separate file `streamlit_app.py` for clarity.
    uvicorn.run(app, host="0.0.0.0", port=8000)
