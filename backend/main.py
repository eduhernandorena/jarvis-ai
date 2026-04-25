import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import edge_tts
from dotenv import load_dotenv
import httpx
from datetime import datetime

# Carrega variáveis do .env
load_dotenv()

import requests
import threading
import base64
import uuid
import re
from fastapi.responses import StreamingResponse
import json

# ========== Configurações de IA ==========
GROQ_MODEL = "llama3-70b-8192"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")

from groq import AsyncGroq

SYSTEM_PROMPT = (
    "Jarvis mode. PT-BR. Direto. Máx 10 palavras.\n"
    "Comandos: {luz_quarto: ligarluzquarto, ar: ligue-o-ar-frio, tv_quarto: ligue-a-tv-do-quarto, tv_sala: ligue-a-tv-da-sala}.\n"
    "Regra: Se ação, use [ALEXA: comando] no início."
)

async def trigger_alexa_webhook(comando: str):
    """
    Envia o comando para a Alexa via Webhook (Padrão: Voice Monkey).
    """
    token = os.getenv("VOICEMONKEY_TOKEN", "")
    secret = os.getenv("VOICEMONKEY_SECRET", "")
    
    if not token:
        print(f"\n[ALEXA SIMULADOR] Comando '{comando}' detectado!\n")
        return

    url = f"https://api-v2.voicemonkey.io/trigger?access_token={token}&secret_token={secret}&device={comando}" if secret else \
          f"https://api-v2.voicemonkey.io/trigger?token={token}&device={comando}"
        
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5)
            print(f"[ALEXA] Webhook disparado. Status: {res.status_code}")
    except Exception as e:
        print(f"[ALEXA] Erro no Webhook: {e}")

app = FastAPI(title="Jarvis Backend MVP")

# Permite comunicação com o frontend (React rodando em outra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

tts_cache = {}

async def generate_speech(text: str) -> str:
    """Gera o áudio a partir do texto usando edge-tts e salva em disco."""
    if text in tts_cache:
        return tts_cache[text]
        
    VOICE = "pt-BR-AntonioNeural"
    os.makedirs("public", exist_ok=True)
    
    output_file = f"public/response_{uuid.uuid4().hex}.mp3"
    
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_file)
    
    with open(output_file, "rb") as f:
        audio_data = f.read()
        
    os.remove(output_file)
    b64 = base64.b64encode(audio_data).decode('utf-8')
    
    tts_cache[text] = b64
    return b64

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    
    async def process_text_stream(stream_gen):
        buffer = ""
        async for text in stream_gen:
            if not text: continue
            buffer += text
            
            # 1. Detectar e disparar comandos Alexa
            alexa_match = re.search(r'\[ALEXA:\s*([^\]]+)\]', buffer)
            if alexa_match:
                comando = alexa_match.group(1).strip()
                asyncio.create_task(trigger_alexa_webhook(comando))
                buffer = buffer.replace(alexa_match.group(0), "")
            
            # 2. Fragmentar em frases para o TTS (Voz)
            match = re.search(r'([.!?]+(?:\s+|$))', buffer)
            if match:
                end_idx = match.end()
                frase = buffer[:end_idx].strip()
                if frase:
                    audio_b64 = await generate_speech(frase)
                    yield json.dumps({"text": frase, "audio": audio_b64}) + "\n"
                buffer = buffer[end_idx:]
        
        # Enviar o que sobrar no buffer
        if buffer.strip():
            audio_b64 = await generate_speech(buffer.strip())
            yield json.dumps({"text": buffer.strip(), "audio": audio_b64}) + "\n"

    async def generate_responses():
        api_key = os.getenv("GROQ_API_KEY", "")
        client_groq = AsyncGroq(api_key=api_key) if api_key else None
        
        try:
            if client_groq:
                async def groq_gen():
                    stream = await client_groq.chat.completions.create(
                        model=GROQ_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT + f"\n\nContexto: {datetime.now().strftime('%d/%m/%Y %H:%M')}"},
                            {"role": "user", "content": request.message}
                        ],
                        stream=True, max_tokens=100, temperature=0.3
                    )
                    async for chunk in stream:
                        yield chunk.choices[0].delta.content or ""
                
                async for chunk in process_text_stream(groq_gen()):
                    yield chunk

            else:
                async def ollama_gen():
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json={
                            "model": OLLAMA_MODEL,
                            "messages": [{"role": "user", "content": request.message}],
                            "stream": True
                        }) as resp:
                            async for line in resp.aiter_lines():
                                if line:
                                    try: yield json.loads(line).get("message", {}).get("content", "")
                                    except: pass
                
                async for chunk in process_text_stream(ollama_gen()):
                    yield chunk
                
        except Exception as e:
            print(f"Erro no streaming: {e}")
            erro_msg = "Falha no processamento da resposta."
            yield json.dumps({"text": erro_msg, "audio": ""}) + "\n"

    return StreamingResponse(generate_responses(), media_type="application/x-ndjson")

# Para servir os arquivos de áudio
from fastapi.staticfiles import StaticFiles

# Certifique-se de que o diretório public existe antes de montar
os.makedirs("public", exist_ok=True)
app.mount("/audio", StaticFiles(directory="public"), name="audio")

# Servir Frontend React compilado
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"status": "Frontend not built yet. Run 'npm run build' in frontend."}
