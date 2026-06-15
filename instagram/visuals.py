"""Geração de visuais (cards) para posts.

Estratégias previstas:
- "template" (implementada aqui): card renderizado por código com Pillow.
- "canva":  gerado via integração Canva pelo assistente (fora deste módulo).
- "ia":     imagem gerada por IA (fora deste módulo).
- "fornecido": você fornece o arquivo de imagem/vídeo.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Proporções nativas do Instagram por formato.
SIZES = {
    "feed": (1080, 1350),      # 4:5
    "carousel": (1080, 1350),  # 4:5
    "story": (1080, 1920),     # 9:16
}

_FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path(_FONT_DIR) / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render_card(
    text: str,
    out_path: str | Path,
    *,
    fmt: str = "feed",
    bg: str = "#1a1a2e",
    accent: str = "#e94560",
    fg: str = "#ffffff",
    handle: str = "@suapagina",
    kicker: str | None = None,
) -> str:
    """Renderiza um único card e salva como JPEG. Devolve o caminho."""
    w, h = SIZES.get(fmt, SIZES["feed"])
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)
    margin = 90
    content_w = w - 2 * margin

    # barra de destaque
    draw.rectangle([margin, margin, margin + 120, margin + 16], fill=accent)
    y = margin + 70

    if kicker:
        kf = _load_font(40, bold=True)
        draw.text((margin, y), kicker.upper(), font=kf, fill=accent)
        y += 80

    title_font = _load_font(72, bold=True)
    for line in _wrap(draw, text, title_font, content_w):
        draw.text((margin, y), line, font=title_font, fill=fg)
        y += 92

    # assinatura no rodapé
    hf = _load_font(36, bold=False)
    draw.text((margin, h - margin - 30), handle, font=hf, fill=accent)

    out_path = str(out_path)
    img.save(out_path, "JPEG", quality=92)
    return out_path


def render_carousel(slides: list[str], out_dir: str | Path, **kwargs) -> list[str]:
    """Renderiza um card por slide e devolve a lista de caminhos."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    total = len(slides)
    for i, slide in enumerate(slides, 1):
        kicker = kwargs.pop("kicker", None) if i == 1 else None
        p = out_dir / f"slide_{i:02d}.jpg"
        render_card(
            slide, p, fmt="carousel",
            kicker=kicker or (f"{i}/{total}" if total > 1 else None),
            **{k: v for k, v in kwargs.items() if k != "kicker"},
        )
        paths.append(str(p))
    return paths
