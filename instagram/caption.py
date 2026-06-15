"""Geração de legenda + hashtags com a Gemini API."""

from __future__ import annotations

import os


def generate_caption(
    brief: str,
    *,
    tone: str = "profissional e acessível",
    lang: str = "pt-BR",
    hashtags: int = 8,
    handle: str | None = None,
) -> str:
    """Gera a legenda de um post de Instagram a partir de um briefing curto.

    Requer a variável de ambiente ``GEMINI_API_KEY``.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada (defina no .env).")

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    assina = f" A página é {handle}." if handle else ""
    prompt = f"""Você é social media de uma página de notícias no Instagram.{assina}
Crie a legenda de um post em {lang}, com tom {tone}.

Briefing: {brief}

Regras:
- Gancho forte na primeira linha (sem clickbait barato).
- 2 a 4 linhas de corpo, escaneáveis, com emojis usados com moderação.
- Termine com uma CTA curta (ex.: salve, comente, compartilhe).
- Acrescente {hashtags} hashtags relevantes ao final, em uma única linha.
Responda apenas com a legenda final, sem comentários extras."""

    return model.generate_content(prompt).text.strip()
