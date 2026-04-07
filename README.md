# News Agent

Agente automatizado que busca notícias diárias sobre tópicos de interesse, gera resumos inteligentes com a **Gemini API** (Google) e envia por email via **Gmail SMTP**.

## Tópicos Configurados

- **Mundo Financeiro** - Mercado financeiro, economia, investimentos, criptomoedas
- **Product Management** - Gestão de produto, estratégias, tendências e melhores práticas

## Como Funciona

1. **Busca notícias** usando a [NewsAPI](https://newsapi.org/) para cada tópico configurado
2. **Gera um resumo** inteligente usando a Gemini API (Google)
3. **Envia por email** via Gmail SMTP com formatação HTML profissional
4. **Executa automaticamente** todo dia às 7h UTC via GitHub Actions

## Configuração

### 1. Obter API Keys

- **NewsAPI**: Cadastre-se em [newsapi.org](https://newsapi.org/) para obter uma chave gratuita
- **Gemini (Google)**: Obtenha sua API key em [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Gmail App Password**: Gere uma senha de app em [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
  - Necessário ter verificação em 2 etapas ativada na conta Google

### 2. Configurar Secrets no GitHub

Vá em **Settings > Secrets and variables > Actions** no repositório e adicione:

| Secret | Descrição |
|--------|-----------|
| `GEMINI_API_KEY` | Chave da API do Gemini (Google) |
| `NEWSAPI_KEY` | Chave da API do NewsAPI |
| `GMAIL_ADDRESS` | Seu endereço Gmail (ex: `seuemail@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Senha de app do Gmail (16 caracteres) |
| `EMAIL_RECIPIENT` | Email que receberá a newsletter |

### 3. Ativar GitHub Actions

O workflow já está configurado para rodar automaticamente. Você também pode executar manualmente:

1. Vá em **Actions** > **Daily News Digest**
2. Clique em **Run workflow**

## Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export GEMINI_API_KEY="sua-chave"
export NEWSAPI_KEY="sua-chave"
export GMAIL_ADDRESS="seu-email@gmail.com"
export GMAIL_APP_PASSWORD="sua-senha-de-app"
export EMAIL_RECIPIENT="destinatario@email.com"

# Executar
python main.py
```

## Personalizar Tópicos

Edite o arquivo `topics.py` para adicionar ou remover tópicos de interesse. Cada tópico tem:

- `name`: Nome do tópico (aparece no email)
- `keywords`: Palavras-chave para busca de notícias
- `description`: Descrição do tópico

## Estrutura do Projeto

```
news_agent/
├── main.py              # Busca notícias + chama Gemini API
├── email_sender.py      # Envia via Gmail SMTP
├── topics.py            # Tópicos de interesse
├── requirements.txt     # Dependências Python
├── README.md            # Este arquivo
└── .github/
    └── workflows/
        └── daily.yml    # Agenda para rodar todo dia às 7h
```
