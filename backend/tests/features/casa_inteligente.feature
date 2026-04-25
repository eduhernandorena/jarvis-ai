# language: pt

Funcionalidade: Inteligência e Automação do Jarvis
  Como um usuário avançado
  Eu quero que o Jarvis entenda comandos complexos e conversas simples
  Para ter um assistente confiável

  Esquema do Cenário: Controle de dispositivos variados
    Dado que o Jarvis está pronto para ouvir
    Quando o usuário diz "<frase>"
    Então o sistema deve disparar o comando "<comando_esperado>" para a Alexa
    E a resposta do Jarvis deve ser curta e direta

    Exemplos:
      | frase                    | comando_esperado         |
      | ligue a luz do quarto    | ligarluzquarto           |
      | apague a luz             | desligarluzquarto        |
      | ligue o ar condicionado  | ligue-o-ar-frio          |
      | desligue o ar            | desligue-o-ar-frio       |
      | ligar tv da sala         | ligue-a-tv-da-sala       |
      | desligar tv do quarto    | desligue-a-tv-do-quarto  |

  Cenário: Conversa amigável sem comandos
    Dado que o Jarvis está pronto para ouvir
    Quando o usuário diz "bom dia Jarvis, como você está?"
    Então a resposta não deve conter nenhuma tag da Alexa
    E a resposta deve ser amigável

  Cenário: Falha no serviço de IA
    Dado que o serviço do Groq está fora do ar
    Quando o usuário diz "olá"
    Então o sistema deve responder com uma mensagem de erro amigável
