# Projeto Jarvis - Assistente de Voz

Este é um MVP para uma interface web de um assistente virtual inspirado no Jarvis do Homem de Ferro. O objetivo é criar uma experiência premium, interativa e fluida, utilizando Inteligência Artificial de ponta.

## 🚀 Tecnologias Utilizadas

### Frontend (O Rosto e Ouvido)
- **React (com TypeScript e Vite):** Para a estrutura da aplicação.
- **CSS Vanilla & Framer Motion:** Para animações avançadas e um design visual impressionante sem depender de frameworks de CSS pesados.
- **Web Speech API:** Utilizada para captura de áudio nativa e transcrição de fala para texto (Speech-to-Text) em tempo real, rodando direto no navegador do usuário de forma gratuita.

### Backend (O Cérebro e a Voz)
- **Python com FastAPI:** Um backend leve e extremamente rápido.
- **Google Gemini API:** O modelo de linguagem (LLM) atuando como o "cérebro" do Jarvis para gerar respostas contextuais e inteligentes.
- **Edge-TTS:** Biblioteca para converter as respostas de texto do Gemini em uma voz fluida e natural (Text-to-Speech).

## 🛠️ Como Executar Localmente

### 1. Requisitos
- Node.js (para o Frontend)
- Python 3.9+ (para o Backend)
- Chave de API do Google Gemini (veja como obter abaixo)

### 2. Configurando o Backend
1. Navegue até a pasta `backend`:
   ```bash
   cd backend
   ```
2. Crie um ambiente virtual e ative:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows use: venv\Scripts\activate
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Crie um arquivo `.env` na pasta `backend` com a sua chave da API:
   ```env
   GEMINI_API_KEY=sua_chave_aqui
   ```
5. Inicie o servidor:
   ```bash
   uvicorn main:app --reload
   ```
   *O backend rodará em `http://localhost:8000`*

### 3. Configurando o Frontend
1. Abra um novo terminal e navegue até a pasta `frontend`:
   ```bash
   cd frontend
   ```
2. Instale as dependências:
   ```bash
   npm install
   ```
3. Inicie a interface web:
   ```bash
   npm run dev
   ```
   *A interface estará disponível em `http://localhost:5173`*

---
Desenvolvido com foco em alta responsividade visual e integração de IA.
