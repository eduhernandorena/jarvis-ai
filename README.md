# 🦾 J.A.R.V.I.S - Intelligent OS MVP

Um assistente virtual híbrido inspirado no Jarvis do Homem de Ferro, integrando **Groq (Llama 3 70B)** para inteligência ultra-rápida, **Edge TTS** para voz natural e automação residencial via **Alexa**.

## 🚀 Principais Tecnologias
- **Frontend**: React + Vite + TypeScript (PWA & Glassmorphism UI)
- **Backend**: FastAPI (Python) + NDJSON Streaming
- **IA**: Groq (Llama 3 70B) & Ollama (Phi3 as backup)
- **Voz**: Web Audio API + Microsoft Edge TTS
- **Automação**: Integração com Alexa via Voice Monkey
- **Testes**: BDD (Behave/Pytest-BDD) para garantia de comportamento

## 📦 Como rodar (Docker)
1. Clone o repositório:
   ```bash
   git clone https://github.com/eduhernandorena/jarvis-ai.git
   ```
2. Configure o `.env` na pasta `backend/`:
   ```env
   GROQ_API_KEY=sua_chave
   VOICEMONKEY_TOKEN=seu_token
   ```
3. Suba o sistema:
   ```bash
   docker-compose up --build
   ```

## 🧪 Testes BDD
Para rodar a suite de testes comportamentais:
```bash
cd backend
python3 -m pytest tests/test_jarvis.py
```

## 📱 Mobile (PWA)
Este projeto é um PWA completo. Basta acessar o URL do frontend no seu celular e selecionar **"Adicionar à Tela de Início"** para ter o Jarvis como um aplicativo nativo com suporte a áudio no iOS e Android.

---
*Desenvolvido para fins de automação residencial inteligente.*
