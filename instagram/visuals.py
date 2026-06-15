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


def _fit_cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Redimensiona/recorta a imagem para preencher ``size`` (estilo CSS cover)."""
    tw, th = size
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def _scrim(size: tuple[int, int], top_alpha: int, bottom_alpha: int) -> Image.Image:
    """Gera um overlay preto com gradiente vertical de transparência (legibilidade)."""
    w, h = size
    overlay = Image.new("L", (1, h))
    for y in range(h):
        a = int(top_alpha + (bottom_alpha - top_alpha) * (y / max(h - 1, 1)))
        overlay.putpixel((0, y), a)
    alpha = overlay.resize((w, h))
    scrim = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    scrim.putalpha(alpha)
    return scrim


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
    background_image: str | Path | None = None,
) -> str:
    """Renderiza um único card e salva como JPEG. Devolve o caminho.

    Se ``background_image`` for informado (ex.: imagem do Magnific), o texto é
    sobreposto a ela com um escurecimento gradiente para garantir legibilidade.
    """
    w, h = SIZES.get(fmt, SIZES["feed"])
    if background_image:
        base = Image.open(background_image).convert("RGBA")
        img = _fit_cover(base, (w, h))
        img = Image.alpha_composite(img, _scrim((w, h), top_alpha=90, bottom_alpha=200))
        img = img.convert("RGB")
    else:
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


def render_carousel(
    slides: list[str],
    out_dir: str | Path,
    *,
    backgrounds: list[str] | None = None,
    kicker: str | None = None,
    **kwargs,
) -> list[str]:
    """Renderiza um card por slide e devolve a lista de caminhos.

    ``backgrounds`` (opcional): lista de imagens de fundo (ex.: do Magnific).
    Se tiver 1 só, é usada em todos os slides; se tiver N, casa 1:1 com os slides.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    total = len(slides)
    for i, slide in enumerate(slides, 1):
        bg_img = None
        if backgrounds:
            bg_img = backgrounds[i - 1] if len(backgrounds) == total else backgrounds[0]
        p = out_dir / f"slide_{i:02d}.jpg"
        render_card(
            slide, p, fmt="carousel",
            kicker=(kicker if i == 1 else (f"{i}/{total}" if total > 1 else None)),
            background_image=bg_img,
            **kwargs,
        )
        paths.append(str(p))
    return paths
