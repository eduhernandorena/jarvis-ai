import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Union
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
import psutil
import logging
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# ========== Configurações de IA ==========
GROQ_MODEL = "llama-3.3-70b-versatile"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
GROQ_FAST_MODEL = "llama-3.1-8b-instant"
GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"


# ========== Configurações de Depuração ==========
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

def log_debug(category, content):
    if DEBUG_MODE:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{'='*20} DEBUG [{timestamp}] [{category}] {'='*20}")
        print(content)
        print(f"{'='*50}\n")

from groq import AsyncGroq

from duckduckgo_search import DDGS
from agent import AGENT_INSTRUCTIONS, ALERT_PROMPT

PERSONALITIES = {
    "jarvis": {
        "voice": "pt-BR-AntonioNeural",
        "prompt": "Jarvis mode. PT-BR. Britânico, sério, leal. Respostas curtas.\n"
                  "Comandos: {luz_quarto: ligarluzquarto, ar: ligue-o-ar-frio, tv_quarto: ligue-a-tv-do-quarto, tv_sala: ligue-a-tv-da-sala}.\n"
                  "Regra: Se ação, use [ALEXA: comando] no início."
    },
    "friday": {
        "voice": "pt-BR-FranciscaNeural",
        "prompt": "Friday mode. PT-BR. Rápida, sarcástica, ultra-eficiente.\n"
                  "Regra: Se ação, use [ALEXA: comando] no início."
    },
    "karen": {
        "voice": "pt-BR-ThalitaNeural",
        "prompt": "Karen mode. PT-BR. Doce, protetora, amigável.\n"
                  "Regra: Se ação, use [ALEXA: comando] no início."
    }
}

async def search_web(query: str):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results)
    except Exception as e:
        print(f"Erro na busca: {e}")
        return "Não consegui pesquisar agora."


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

MEMORY_FILE = "memory.json"

def get_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

async def update_memory_task(user_msg, jarvis_msg):
    """Analisa se há novos fatos para lembrar e atualiza o JSON"""
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key: return
        
        client = AsyncGroq(api_key=api_key)
        memory = get_memory()
        
        prompt = (
            f"Extraia fatos novos e permanentes sobre o usuário desta conversa.\n"
            f"Memória atual: {json.dumps(memory)}\n"
            f"Usuário: {user_msg}\n"
            f"Jarvis: {jarvis_msg}\n"
            f"Responda APENAS o JSON atualizado com os novos fatos."
        )
        
        res = await client.chat.completions.create(
            model=GROQ_FAST_MODEL, # Modelo menor e mais barato para tarefas de background
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        new_memory = json.loads(res.choices[0].message.content)
        if new_memory:
            save_memory(new_memory)
    except Exception as e:
        print(f"Erro ao atualizar memória: {e}")

app = FastAPI(title="Jarvis Backend MVP")


# Permite comunicação com o frontend (React rodando em outra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite todas as origens (ideal para testes com túnel)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Monitoramento e Telemetria ==========

# Configuração de Logging para Rastreabilidade
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("jarvis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis")

# Prometheus Telemetria
Instrumentator().instrument(app).expose(app)

# OpenTelemetry Traceability (Console por enquanto para debug)
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
FastAPIInstrumentor.instrument_app(app)

@app.get("/api/stats")
async def get_system_stats():
    """Retorna estatísticas de uso do sistema para o monitor de recursos."""
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "ram_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "uptime": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Placeholder simplificado
    }

class ChatRequest(BaseModel):
    message: str
    image: Optional[str] = None
    personality: Optional[str] = "jarvis"

GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"

tts_cache = {}

async def generate_speech(text: str, personality: str = "jarvis") -> str:
    """Gera o áudio a partir do texto, limpando formatações visuais."""
    # Limpa markdown para a voz não ler símbolos
    text_clean = re.sub(r'[\*\#\_\[\]\(\)\>]', '', text)
    text_clean = text_clean.replace('•', '').replace('-', ' ')
    
    cache_key = f"{personality}:{text_clean}"
    if cache_key in tts_cache:
        return tts_cache[cache_key]
        
    voice = PERSONALITIES.get(personality, PERSONALITIES["jarvis"])["voice"]
    os.makedirs("public", exist_ok=True)
    
    output_file = f"public/response_{uuid.uuid4().hex}.mp3"
    
    communicate = edge_tts.Communicate(text_clean, voice)
    await communicate.save(output_file)
    
    with open(output_file, "rb") as f:
        audio_data = f.read()
        
    os.remove(output_file)
    b64 = base64.b64encode(audio_data).decode('utf-8')
    
    tts_cache[cache_key] = b64
    return b64


async def get_ai_response(message: str, personality: str = "jarvis", image: Optional[str] = None):
    """Lógica central para obter resposta da IA (Groq ou Ollama)."""
    api_key = os.getenv("GROQ_API_KEY", "")
    client_groq = AsyncGroq(api_key=api_key) if api_key else None
    
    search_results = ""
    if client_groq:
        try:
            check_res = await client_groq.chat.completions.create(
                model=GROQ_FAST_MODEL,
                messages=[{"role": "user", "content": f"O usuário perguntou: '{message}'. Ele quer saber de fatos, notícias, clima ou algo que mude com o tempo (hoje, agora, notícias)? Responda APENAS 'Sim' ou 'Não'."}],
                max_tokens=5, temperature=0
            )
            if "sim" in check_res.choices[0].message.content.lower():
                search_results = await search_web(message)
        except Exception as e:
            print(f"Erro na pré-busca: {e}")

    if client_groq:
        model = GROQ_VISION_MODEL if image else GROQ_MODEL
        memory = get_memory()
        memory_str = f"\nO que você sabe sobre o usuário: {json.dumps(memory)}" if memory else ""
        search_str = f"\nRESULTADOS DA WEB: {search_results}" if search_results else ""
        p_prompt = AGENT_INSTRUCTIONS + f"\nVOCÊ ESTÁ OPERANDO COMO: {personality.upper()}"
        
        messages = [
            {"role": "system", "content": p_prompt + f"\nContexto Atual: {datetime.now().strftime('%d/%m/%Y %H:%M')}" + memory_str + search_str},
            {"role": "user", "content": [{"type": "text", "text": message}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}] if image else message}
        ]

        res = await client_groq.chat.completions.create(
            model=model, messages=messages, max_tokens=300, temperature=0.5
        )
        full_text = res.choices[0].message.content
        asyncio.create_task(update_memory_task(message, full_text))
        return full_text
    else:
        # Fallback Ollama
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json={
                "model": OLLAMA_MODEL,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            })
            return resp.json().get("message", {}).get("content", "")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    
    async def process_full_response(full_text):
        # 1. Comandos Alexa
        alexa_match = re.search(r'\[ALEXA:\s*([^\]]+)\]', full_text)
        if alexa_match:
            comando = alexa_match.group(1).strip()
            asyncio.create_task(trigger_alexa_webhook(comando))
            full_text = full_text.replace(alexa_match.group(0), "")

        # 2. Envia o TEXTO COMPLETO primeiro
        yield json.dumps({"text": full_text, "audio": ""}) + "\n"

        # 3. Gera o áudio completo
        frases = re.split(r'(?<=[.!?])\s+', full_text)
        for frase in frases:
            if frase.strip():
                audio_b64 = await generate_speech(frase.strip(), request.personality)
                yield json.dumps({"text": "", "audio": audio_b64}) + "\n"

    async def generate_responses():
        try:
            full_text = await get_ai_response(request.message, request.personality, request.image)
            async for chunk in process_full_response(full_text):
                yield chunk
        except Exception as e:
            print(f"Erro no chat: {e}")
            yield json.dumps({"text": "Erro no processamento.", "audio": ""}) + "\n"

    return StreamingResponse(generate_responses(), media_type="application/x-ndjson")

    return StreamingResponse(generate_responses(), media_type="application/x-ndjson")


@app.get("/api/alerts")
async def get_alerts():
    """Retorna alertas interpretados por IA usando Feed RSS estável"""
    try:
        api_key = os.getenv("GROQ_API_KEY", "")
        client = AsyncGroq(api_key=api_key) if api_key else None
        
        # 1. Captura Notícias via RSS (G1 Tecnologia - Muito estável)
        raw_news = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as h_client:
                # Pegando o RSS de tecnologia
                resp = await h_client.get("https://g1.globo.com/dynamo/tecnologia/rss2.xml")
                if resp.status_code == 200:
                    # Extrai os títulos usando Regex simples (dentro das tags <title>)
                    raw_news = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', resp.text)
                    # Remove o primeiro título que geralmente é o nome do site
                    if raw_news: raw_news.pop(0)
                    raw_news = raw_news[:6] # Pega as 6 principais
        except Exception as e:
            print(f"Erro no RSS: {e}")

        if not raw_news or not client:
            return {"alert": "[SISTEMA: ONLINE]\n• STATUS: OPERANTE\n• AMBIENTE: ESTÁVEL\n• AGUARDANDO COMANDOS"}

        # 2. IA gera o briefing HUD baseado no ALERT_PROMPT
        log_debug("ALERT PROMPT", f"Manchetes: {', '.join(raw_news)}")
        res = await client.chat.completions.create(
            model=GROQ_FAST_MODEL,
            messages=[{"role": "system", "content": ALERT_PROMPT},
                      {"role": "user", "content": f"Briefing sobre estas manchetes: {', '.join(raw_news)}"}],
            max_tokens=250, temperature=0.3
        )
        
        log_debug("ALERT RESPONSE", res.choices[0].message.content)
        return {"alert": res.choices[0].message.content.strip()}


    except Exception as e:
        print(f"Erro crítico no Alerta: {e}")
        return {"alert": "[STATUS: OK]\n• SISTEMAS: ATIVOS\n• NÚCLEO: OPERANTE"}








# ========== Integração Alexa (Skill Endpoint) ==========

@app.post("/api/alexa/skill")
async def alexa_skill(request: dict):
    """
    Endpoint para integração com Amazon Alexa Skill.
    Recebe requisições de Intent e responde usando o cérebro Jarvis.
    """
    try:
        req_type = request.get("request", {}).get("type")
        
        if req_type == "LaunchRequest":
            speech = "Jarvis online. Como posso ajudar, senhor?"
        elif req_type == "IntentRequest":
            intent_name = request["request"]["intent"]["name"]
            
            if intent_name == "AskJarvisIntent":
                user_msg = request["request"]["intent"]["slots"]["question"]["value"]
                # Chama a IA de forma síncrona (esperando o texto completo)
                speech = await get_ai_response(user_msg, "jarvis")
            else:
                speech = "Desculpe, não conheço esse comando."
        else:
            speech = "Sistema Jarvis em modo de espera."

        return {
            "version": "1.0",
            "response": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": speech
                },
                "shouldEndSession": True
            }
        }
    except Exception as e:
        print(f"Erro Alexa Skill: {e}")
        return {"version": "1.0", "response": {"outputSpeech": {"type": "PlainText", "text": "Houve um erro no meu núcleo de processamento."}}}

# Para servir os arquivos de áudio

app.mount("/audio", StaticFiles(directory="public"), name="audio")

# Servir Frontend React compilado
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"status": "Frontend not built yet. Run 'npm run build' in frontend."}

if __name__ == "__main__":
    import uvicorn
    # Inicia o servidor na porta 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
