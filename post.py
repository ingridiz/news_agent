#!/usr/bin/env python3
"""Orquestrador de postagem no Instagram via Zernio.

Fluxo: briefing -> legenda (Gemini) + visual -> rascunho/agendamento/publicação.

Exemplos:
  # 1) Rascunho de carrossel com cards de template (não publica; gera preview)
  python post.py --brief "Alta do dólar hoje" --format carousel \
      --slide "Dólar bate R$6,10" --slide "Veja o que puxou a alta" \
      --mode draft

  # 2) Publicar imediatamente uma imagem que você já tem
  python post.py --caption "Texto do post" --media foto.jpg \
      --format feed --mode now

  # 3) Agendar um story para um horário (ISO 8601, UTC)
  python post.py --media card.jpg --format story \
      --mode schedule --when 2026-06-16T12:00:00Z

  # Inspecionar o JSON exato sem chamar a API:
  python post.py ... --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DRAFTS_DIR = Path(__file__).parent / "drafts"


def _load_dotenv() -> None:
    """Carrega variáveis do .env (sem dependência externa)."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        import os

        os.environ.setdefault(key.strip(), value.strip())


def build_visuals(args) -> list[str]:
    """Devolve a lista de arquivos de mídia para o post."""
    if args.media:
        return list(args.media)  # estratégia "fornecido"

    # estratégia "template" (Pillow)
    from instagram import visuals

    work = DRAFTS_DIR / args.slug / "media"
    work.mkdir(parents=True, exist_ok=True)
    backgrounds = args.background or None  # imagens de fundo (ex.: Magnific)

    if args.format == "carousel":
        slides = args.slide or [args.brief or "Sem texto"]
        return visuals.render_carousel(
            slides, work, backgrounds=backgrounds,
            handle=args.handle, kicker=args.kicker,
        )

    text = (args.slide[0] if args.slide else None) or args.brief or "Sem texto"
    out = work / "card.jpg"
    return [visuals.render_card(
        text, out, fmt=args.format, handle=args.handle, kicker=args.kicker,
        background_image=(backgrounds[0] if backgrounds else None),
    )]


def build_caption(args) -> str:
    if args.caption is not None:
        return args.caption
    if not args.brief:
        return ""
    from instagram.caption import generate_caption

    return generate_caption(args.brief, handle=args.handle)


def main() -> int:
    _load_dotenv()
    p = argparse.ArgumentParser(description="Postagem no Instagram via Zernio")
    p.add_argument("--brief", help="Briefing curto para gerar legenda/visual")
    p.add_argument("--caption", help="Legenda explícita (pula a IA)")
    p.add_argument("--slide", action="append", help="Texto de um card (repita p/ carrossel)")
    p.add_argument("--media", action="append", help="Arquivo de mídia já pronto (repita)")
    p.add_argument("--background", action="append",
                   help="Imagem de fundo do card, ex.: gerada no Magnific (repita p/ carrossel)")
    p.add_argument("--format", default="feed",
                   choices=["feed", "carousel", "reel", "story"])
    p.add_argument("--mode", default="draft",
                   choices=["draft", "zdraft", "now", "schedule"],
                   help="draft=preview local | zdraft=rascunho no Zernio (não publica) "
                        "| now=publica já | schedule=agenda")
    p.add_argument("--when", help="Horário ISO 8601 para --mode schedule (ex.: 2026-06-16T09:00:00)")
    p.add_argument("--timezone", default="America/Sao_Paulo",
                   help="Fuso do agendamento (default: America/Sao_Paulo)")
    p.add_argument("--account-id", help="ID da conta IG no Zernio (auto-detecta se omitido)")
    p.add_argument("--handle", default="@suapagina", help="@ exibido nos cards")
    p.add_argument("--kicker", help="Chapéu/etiqueta no topo do card")
    p.add_argument("--dry-run", action="store_true", help="Mostra o payload sem publicar")
    args = p.parse_args()

    args.slug = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    if args.format == "reel" and not args.media:
        p.error("Reel exige um vídeo: use --media arquivo.mp4")

    # 1) Visual + legenda
    media_files = build_visuals(args)
    caption = build_caption(args)

    print(f"[INFO] Formato: {args.format} | Modo: {args.mode}")
    print(f"[INFO] Mídia gerada/usada ({len(media_files)}):")
    for m in media_files:
        print(f"        - {m}")
    print("[INFO] Legenda:")
    print("        " + (caption.replace("\n", "\n        ") if caption else "(vazia)"))

    # 2) Modo rascunho: salva manifest e para (sem rede)
    if args.mode == "draft":
        manifest = {
            "created_at": args.slug,
            "format": args.format,
            "caption": caption,
            "media": [str(m) for m in media_files],
        }
        mpath = DRAFTS_DIR / args.slug / "manifest.json"
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        print(f"\n[OK] Rascunho salvo em {mpath}")
        print("     Revise o preview e rode de novo com --mode now ou --mode schedule.")
        return 0

    # 3) Publicar/agendar via Zernio
    from instagram.zernio_client import ZernioClient, ZernioError

    try:
        client = ZernioClient()
        account_id = args.account_id
        if not account_id and not args.dry_run:
            acc = client.find_instagram_account()
            if not acc:
                print("[ERRO] Nenhuma conta de Instagram conectada no Zernio.", file=sys.stderr)
                return 1
            account_id = client.account_id(acc)
            print(f"[INFO] Conta IG detectada: {acc.get('username')} ({account_id})")

        media_urls = []
        if not args.dry_run:
            for m in media_files:
                print(f"[INFO] Upload: {m}")
                media_urls.append(client.upload_media(m))
        else:
            media_urls = [f"file://{m}" for m in media_files]

        result = client.create_post(
            account_id=account_id or "AUTO",
            caption=caption,
            media_urls=media_urls,
            ig_type=args.format,
            publish_now=(args.mode == "now"),
            scheduled_for=(args.when if args.mode == "schedule" else None),
            timezone=(args.timezone if args.mode == "schedule" else None),
            dry_run=args.dry_run,
        )
        print("\n[OK] Resultado:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ZernioError as e:
        print(f"[ERRO Zernio] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
