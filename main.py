"""
News Agent - Busca notícias e gera resumos com a Gemini API.
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

import google.generativeai as genai

from topics import TOPICS
from email_sender import send_email


def fetch_news(topic: dict) -> list[dict]:
    """Busca notícias usando a NewsAPI para um tópico específico."""
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        print(f"[WARN] NEWSAPI_KEY não configurada. Pulando busca para '{topic['name']}'.")
        return []

    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    query = " OR ".join(topic["keywords"][:5])
    params = urllib.parse.urlencode(
        {
            "q": query,
            "from": yesterday,
            "sortBy": "relevancy",
            "language": "pt",
            "pageSize": 10,
            "apiKey": api_key,
        }
    )

    url = f"https://newsapi.org/v2/everything?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NewsAgent/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Falha ao buscar notícias para '{topic['name']}': {e}")
        return []

    articles = data.get("articles", [])
    return [
        {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "source": a.get("source", {}).get("name", ""),
            "publishedAt": a.get("publishedAt", ""),
        }
        for a in articles
        if a.get("title")
    ]


def summarize_with_gemini(all_news: dict[str, list[dict]]) -> str:
    """Usa a Gemini API para gerar um resumo das notícias agrupadas por tópico."""
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")

    news_text = ""
    for topic_name, articles in all_news.items():
        if not articles:
            continue
        news_text += f"\n\n## {topic_name}\n"
        for i, article in enumerate(articles, 1):
            news_text += (
                f"\n{i}. **{article['title']}**\n"
                f"   Fonte: {article['source']}\n"
                f"   Resumo: {article['description']}\n"
                f"   Link: {article['url']}\n"
            )

    if not news_text.strip():
        return "Nenhuma notícia encontrada para os tópicos de hoje."

    prompt = f"""Você é um assistente que cria newsletters diárias em português brasileiro.

Analise as notícias abaixo e crie um resumo bem estruturado e envolvente para cada tópico.
Para cada tópico:
- Destaque as 3-5 notícias mais relevantes
- Faça um breve comentário sobre cada uma
- Inclua os links originais
- Use um tom profissional mas acessível

Formato: Use HTML para formatação (será enviado por email).
Inclua um cabeçalho com a data de hoje: {datetime.utcnow().strftime("%d/%m/%Y")}

Notícias do dia:
{news_text}"""

    response = model.generate_content(prompt)

    return response.text


def main():
    """Fluxo principal do agente de notícias."""
    print(f"[INFO] Iniciando agente de notícias - {datetime.utcnow().isoformat()}")

    # 1. Buscar notícias para cada tópico
    all_news: dict[str, list[dict]] = {}
    for topic in TOPICS:
        print(f"[INFO] Buscando notícias: {topic['name']}...")
        articles = fetch_news(topic)
        all_news[topic["name"]] = articles
        print(f"[INFO] Encontradas {len(articles)} notícias para '{topic['name']}'")

    # 2. Gerar resumo com Gemini
    print("[INFO] Gerando resumo com Gemini...")
    summary = summarize_with_gemini(all_news)
    print("[INFO] Resumo gerado com sucesso!")

    # 3. Enviar por email
    recipient = os.environ.get("EMAIL_RECIPIENT")
    if not recipient:
        print("[WARN] EMAIL_RECIPIENT não configurado. Imprimindo resumo no console.")
        print("\n" + "=" * 60)
        print(summary)
        print("=" * 60)
        return

    today = datetime.utcnow().strftime("%d/%m/%Y")
    subject = f"Daily News Digest - {today}"

    print(f"[INFO] Enviando email para {recipient}...")
    send_email(
        recipient=recipient,
        subject=subject,
        body_html=summary,
    )
    print("[INFO] Email enviado com sucesso!")


if __name__ == "__main__":
    main()
