# Instagram Automation (Zernio)

Automação de postagem no Instagram comandada por chat: você descreve o post,
o agente gera **legenda** (Gemini) + **visual** e publica/agenda via a
[API do Zernio](https://docs.zernio.com).

## Fluxo

```
briefing (chat)  ->  legenda (Gemini) + visual  ->  rascunho / publicar / agendar
```

- **Visual:** template (Pillow), Canva, IA ou arquivo fornecido por você.
- **Formatos:** feed, carrossel, story, reel (reel exige vídeo).
- **Publicação:** rascunho para aprovação, agendamento ou publicação imediata.

## Estrutura

```
news_agent/
├── post.py                    # CLI orquestrador
├── instagram/
│   ├── zernio_client.py       # cliente da API do Zernio
│   ├── caption.py             # legenda + hashtags via Gemini
│   └── visuals.py             # cards (feed/carrossel/story) via Pillow
├── requirements.txt
└── drafts/                    # rascunhos + mídia gerada (gitignored)
```

## Configuração

1. **Instalar dependências:** `pip install -r requirements.txt`
2. **Variáveis de ambiente** (arquivo `.env`, já no `.gitignore`):

   | Variável | Descrição |
   |----------|-----------|
   | `ZERNIO_API_KEY` | Chave da API do Zernio (`sk_...`). Settings → API Keys |
   | `GEMINI_API_KEY` | Chave do Gemini (só para gerar legenda com IA) |

3. **Conectar o Instagram no Zernio** (uma vez): criar um *profile*, conectar a
   conta **Business/Creator** via OAuth e anotar o `_id` da conta.

> **Atenção (ambiente remoto):** se rodar pelo Claude Code na web, adicione
> `zernio.com` ao *allowlist* de egress do ambiente para liberar as chamadas à API.

## Uso

```bash
# Rascunho de carrossel (gera preview, não publica)
python post.py --brief "Alta do dólar hoje" --format carousel \
    --slide "Dólar bate R$6,10" --slide "O que puxou a alta" \
    --handle "@suapagina" --kicker "Economia" --mode draft

# Publicar imediatamente uma imagem pronta
python post.py --caption "Texto do post" --media foto.jpg --format feed --mode now

# Agendar um story
python post.py --media card.jpg --format story \
    --mode schedule --when "2026-06-16T09:00:00" --timezone "America/Sao_Paulo"

# Inspecionar o JSON exato sem chamar a API
python post.py ... --dry-run
```

### Principais flags

| Flag | Função |
|------|--------|
| `--brief` | Briefing para gerar legenda/visual |
| `--caption` | Legenda explícita (pula a IA) |
| `--slide` | Texto de um card (repita para carrossel) |
| `--media` | Arquivo de mídia já pronto (repita) |
| `--format` | `feed` \| `carousel` \| `reel` \| `story` |
| `--mode` | `draft` \| `now` \| `schedule` |
| `--when` / `--timezone` | Horário e fuso do agendamento |
| `--dry-run` | Mostra o payload sem publicar |
