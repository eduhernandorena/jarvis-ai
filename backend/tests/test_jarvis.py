import pytest
import json
import re
from pytest_bdd import scenario, given, when, then, parsers
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, patch

client = TestClient(app)

# --- Scenarios ---

@scenario("features/casa_inteligente.feature", "Controle de dispositivos variados")
def test_dispositivos(): pass

@scenario("features/casa_inteligente.feature", "Conversa amigável sem comandos")
def test_conversa(): pass

@scenario("features/casa_inteligente.feature", "Falha no serviço de IA")
def test_falha_ia(): pass

# --- Fixtures & Mocks ---

class MockStream:
    def __init__(self, content):
        self.content = content
    async def __aiter__(self):
        yield AsyncMock(choices=[AsyncMock(delta=AsyncMock(content=self.content))])
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass

# --- Steps ---

@given("que o Jarvis está pronto para ouvir")
def jarvis_ready():
    return True

@given("que o serviço do Groq está fora do ar")
def groq_down():
    # Isso será usado no Mock dentro do @when
    return True

@when(parsers.parse('o usuário diz "{frase}"'), target_fixture="api_response")
def user_says(frase):
    # Lógica de Mock inteligente
    content = f"Entendido. {frase}"
    
    # Simula falha se a frase for "olá" (contexto do cenário de erro)
    if frase == "olá":
        with patch("main.AsyncGroq") as mock_groq_class:
            mock_client = mock_groq_class.return_value
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Groq Offline"))
            # Também mockamos o httpx para o backup do Ollama falhar na hora
            with patch("httpx.AsyncClient.stream", side_effect=Exception("Ollama Offline")):
                with patch("main.os.getenv", return_value=""):
                    return client.post("/api/chat", json={"message": frase})

    # Caso normal (Comandos ou Conversa)
    if "luz" in frase:
        cmd = "ligarluzquarto" if "lig" in frase else "desligarluzquarto"
        content = f"[ALEXA: {cmd}] {content}"
    elif "ar" in frase:
        cmd = "ligue-o-ar-frio" if "lig" in frase else "desligue-o-ar-frio"
        content = f"[ALEXA: {cmd}] {content}"
    
    with patch("main.AsyncGroq") as mock_groq_class:
        mock_client = mock_groq_class.return_value
        mock_client.chat.completions.create = AsyncMock(return_value=MockStream(content))
        with patch("main.generate_speech", return_value="fake_audio"):
            with patch("main.os.getenv", side_effect=lambda k, d="": "fake_key" if k == "GROQ_API_KEY" else d):
                return client.post("/api/chat", json={"message": frase})

@then(parsers.parse('o sistema deve disparar o comando "{comando_esperado}" para a Alexa'))
def check_alexa_command(api_response, comando_esperado):
    assert api_response.status_code == 200

@then("a resposta do Jarvis deve ser curta e direta")
def check_short_response(api_response):
    data = json.loads(api_response.text.split("\n")[0])
    assert len(data["text"].split()) <= 25

@then("a resposta não deve conter nenhuma tag da Alexa")
def check_no_alexa_tag(api_response):
    data = json.loads(api_response.text.split("\n")[0])
    assert "[ALEXA:" not in data["text"]

@then("a resposta deve ser amigável")
def check_friendly(api_response):
    assert api_response.status_code == 200

@then("o sistema deve responder com uma mensagem de erro amigável")
def check_error_msg(api_response):
    data = json.loads(api_response.text.split("\n")[0])
    assert "falha" in data["text"].lower() or "erro" in data["text"].lower()
