# ChangeLog - Projeto Jarvis

Este arquivo documenta as mudanças e evolução do projeto durante seu desenvolvimento.

## [🚀 MVP Fase 1] - Concluído
- **Arquitetura**: Definição da stack híbrida (FastAPI + React + Docker).
- **Backend**: 
    - Implementação de rotas assíncronas com FastAPI.
    - Integração com **Groq API** (Llama 3.3/3.1) para inteligência.
    - Suporte a **Ollama** como backup local.
    - Sistema de **Streaming NDJSON** para texto e áudio simultâneos.
    - Integração com **Edge TTS** para vozes neurais brasileiras.
- **Frontend**:
    - Criação da interface **HUD futurista** com Glassmorphism.
    - Implementação de animações fluidas com **Framer Motion**.
    - Suporte a **PWA** (Progressive Web App).
    - Integração com **Capacitor.js** para builds mobile nativos.
- **Documentação**:
    - `README.md` completo com diagramas e mockups.
    - Criação do `changeList.md`.

## [🧠 MVP Fase 2] - Em desenvolvimento
- **[Adicionado]** Sistema de **Memória Inteligente**: Extração automática de fatos do usuário para persistência em JSON.
- **[Adicionado]** Suporte a **Visão Computacional**: Processamento de imagens com Llama 3.2 Vision.
- **[Adicionado]** Integração **Alexa/Voice Monkey**: Comandos de voz que disparam rotinas de automação residencial.
- **[Adicionado]** Busca Web em tempo real via DuckDuckGo.
- **[Adicionado]** Personas Dinâmicas: Alternância entre Jarvis, Friday e Karen com mudanças de voz e personalidade.

## [🧪 Qualidade & Testes]
- **[Adicionado]** Suite de testes BDD com **Pytest-BDD** para validação de comportamento do assistente.

## [🛠 Próximos Passos]
- Integração com Spotify API para controle de música.
- Dashboard de monitoramento de recursos do sistema.
- Melhoria no sistema de reconhecimento de voz contínuo (Always-on).
- Suporte a ferramentas (Function Calling) mais complexas.
