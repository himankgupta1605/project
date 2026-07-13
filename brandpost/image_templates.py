"""Pillow-based rendering engine for static posts and carousels.

Every template is themed purely from the Brand object (colors, fonts, logo),
so the same code produces on-brand output for any brand fed into it.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from brandpost.caption_generator import Slide
from brandpost.config import PORTRAIT_SIZE, SQUARE_SIZE
from brandpost.fonts import get_font
from brandpost.models import Brand
from brandpost.storage import new_post_slide_path

MARGIN = 80


# --------------------------------------------------------------- colors --

def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(c * 2 for c in color)
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_text_color(bg_hex: str) -> tuple[int, int, int]:
    lum = relative_luminance(hex_to_rgb(bg_hex))
    return (20, 20, 20) if lum > 0.5 else (250, 250, 250)


def mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ------------------------------------------------------------ background --

def solid_background(size: tuple[int, int], color_hex: str) -> Image.Image:
    return Image.new("RGB", size, hex_to_rgb(color_hex))


def gradient_background(size: tuple[int, int], top_hex: str, bottom_hex: str) -> Image.Image:
    top, bottom = hex_to_rgb(top_hex), hex_to_rgb(bottom_hex)
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    height = size[1]
    for y in range(height):
        draw.line([(0, y), (size[0], y)], fill=mix(top, bottom, y / max(height - 1, 1)))
    return img


# ------------------------------------------------------------------ text --

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    brand: Brand,
    max_width: int,
    max_height: int,
    start_size: int,
    min_size: int = 22,
    weight: str = "bold",
    line_spacing: float = 1.2,
):
    size = start_size
    while size >= min_size:
        font = get_font(brand, weight, size)
        lines = wrap_text(draw, text, font, max_width)
        line_h = int((font.getbbox("Ag")[3] - font.getbbox("Ag")[1]) * line_spacing)
        if line_h * len(lines) <= max_height:
            return font, lines, line_h
        size -= 4
    font = get_font(brand, weight, min_size)
    lines = wrap_text(draw, text, font, max_width)
    line_h = int((font.getbbox("Ag")[3] - font.getbbox("Ag")[1]) * line_spacing)
    return font, lines, line_h


def draw_multiline_centered(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font,
    box: tuple[int, int, int, int],
    fill,
    line_h: int,
    align: str = "center",
):
    x0, y0, x1, y1 = box
    total_h = line_h * len(lines)
    y = y0 + max((y1 - y0) - total_h, 0) / 2
    for line in lines:
        w = draw.textlength(line, font=font)
        if align == "center":
            x = x0 + ((x1 - x0) - w) / 2
        elif align == "right":
            x = x1 - w
        else:
            x = x0
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h


# ------------------------------------------------------------- chrome ----

def paste_logo(canvas: Image.Image, brand: Brand, position: str = "top-center", max_height: int = 84):
    if not brand.logo_path or not Path(brand.logo_path).exists():
        return
    try:
        logo = Image.open(brand.logo_path).convert("RGBA")
    except Exception:
        return
    ratio = max_height / logo.height
    logo = logo.resize((max(1, int(logo.width * ratio)), max_height))
    w, h = canvas.size
    lw, lh = logo.size
    positions = {
        "top-center": ((w - lw) // 2, MARGIN),
        "top-left": (MARGIN, MARGIN),
        "top-right": (w - MARGIN - lw, MARGIN),
        "bottom-center": ((w - lw) // 2, h - MARGIN - lh),
    }
    canvas.paste(logo, positions.get(position, positions["top-center"]), logo)


def draw_handle(draw: ImageDraw.ImageDraw, brand: Brand, canvas_size, fill):
    if not brand.handle:
        return
    font = get_font(brand, "regular", 28)
    text = brand.handle if brand.handle.startswith("@") else f"@{brand.handle}"
    w = draw.textlength(text, font=font)
    x = (canvas_size[0] - w) / 2
    y = canvas_size[1] - MARGIN - 10
    draw.text((x, y), text, font=font, fill=fill)


def draw_page_dots(draw: ImageDraw.ImageDraw, canvas_size, index: int, total: int, active, inactive):
    if total <= 1:
        return
    r = 6
    gap = 20
    total_w = total * gap
    x0 = (canvas_size[0] - total_w) / 2
    y = canvas_size[1] - MARGIN - 44
    for i in range(total):
        cx = x0 + i * gap + gap / 2
        color = active if i == index else inactive
        draw.ellipse([cx - r, y - r, cx + r, y + r], fill=color)


def draw_badge(draw: ImageDraw.ImageDraw, brand: Brand, xy, number: int, bg, fg):
    r = 34
    x, y = xy
    draw.ellipse([x - r, y - r, x + r, y + r], fill=bg)
    font = get_font(brand, "bold", 30)
    text = str(number)
    w = draw.textlength(text, font=font)
    bbox = font.getbbox(text)
    h = bbox[3] - bbox[1]
    draw.text((x - w / 2, y - h / 2 - bbox[1]), text, font=font, fill=fg)


# ------------------------------------------------------------- templates -

def render_quote_slide(brand: Brand, slide: Slide, size: tuple[int, int] = SQUARE_SIZE) -> Image.Image:
    canvas = solid_background(size, brand.accent_color)
    draw = ImageDraw.Draw(canvas)
    text_color = readable_text_color(brand.accent_color)

    mark_font = get_font(brand, "serif_bold", 220)
    draw.text((MARGIN - 10, MARGIN - 60), "“", font=mark_font, fill=text_color)

    box = (MARGIN, size[1] * 0.28, size[0] - MARGIN, size[1] * 0.72)
    font, lines, line_h = fit_text(
        draw, slide.heading, brand, int(box[2] - box[0]), int(box[3] - box[1]),
        start_size=88, weight="bold",
    )
    draw_multiline_centered(draw, lines, font, box, text_color, line_h)

    if slide.body:
        body_font = get_font(brand, "regular", 34)
        body_lines = wrap_text(draw, slide.body.upper(), body_font, size[0] - 2 * MARGIN)
        draw_multiline_centered(
            draw, body_lines, body_font,
            (MARGIN, size[1] * 0.78, size[0] - MARGIN, size[1] * 0.86),
            text_color, 44,
        )

    paste_logo(canvas, brand, "top-center")
    draw_handle(draw, brand, size, text_color)
    return canvas


def render_stat_slide(brand: Brand, slide: Slide, size: tuple[int, int] = SQUARE_SIZE) -> Image.Image:
    canvas = solid_background(size, brand.background_color)
    draw = ImageDraw.Draw(canvas)
    text_color = hex_to_rgb(brand.text_color)
    accent = hex_to_rgb(brand.accent_color)

    paste_logo(canvas, brand, "top-center")

    box = (MARGIN, size[1] * 0.30, size[0] - MARGIN, size[1] * 0.66)
    font, lines, line_h = fit_text(
        draw, slide.heading, brand, int(box[2] - box[0]), int(box[3] - box[1]),
        start_size=150, weight="bold",
    )
    draw_multiline_centered(draw, lines, font, box, accent, line_h)

    draw.rectangle([size[0] / 2 - 60, size[1] * 0.68, size[0] / 2 + 60, size[1] * 0.68 + 6], fill=accent)

    if slide.body:
        body_font = get_font(brand, "regular", 40)
        body_lines = wrap_text(draw, slide.body, body_font, size[0] - 2 * MARGIN)
        draw_multiline_centered(
            draw, body_lines, body_font,
            (MARGIN, size[1] * 0.72, size[0] - MARGIN, size[1] * 0.88),
            text_color, 52,
        )

    draw_handle(draw, brand, size, text_color)
    return canvas


def render_carousel_slide(
    brand: Brand, slide: Slide, index: int, total: int, size: tuple[int, int] = PORTRAIT_SIZE
) -> Image.Image:
    is_hook = index == 0
    is_cta = index == total - 1

    if is_hook:
        canvas = solid_background(size, brand.primary_color)
        text_color = readable_text_color(brand.primary_color)
    elif is_cta:
        canvas = solid_background(size, brand.accent_color)
        text_color = readable_text_color(brand.accent_color)
    else:
        canvas = solid_background(size, brand.background_color)
        text_color = hex_to_rgb(brand.text_color)

    draw = ImageDraw.Draw(canvas)
    paste_logo(canvas, brand, "top-center")

    if is_hook:
        box = (MARGIN, size[1] * 0.32, size[0] - MARGIN, size[1] * 0.68)
        font, lines, line_h = fit_text(draw, slide.heading, brand, int(box[2] - box[0]), int(box[3] - box[1]), start_size=96, weight="bold")
        draw_multiline_centered(draw, lines, font, box, text_color, line_h)
        hint_font = get_font(brand, "regular", 30)
        hint = "SWIPE  →"
        w = draw.textlength(hint, font=hint_font)
        draw.text(((size[0] - w) / 2, size[1] * 0.80), hint, font=hint_font, fill=text_color)

    elif is_cta:
        handle_text = brand.handle if brand.handle.startswith("@") else f"@{brand.handle}" if brand.handle else brand.name
        box = (MARGIN, size[1] * 0.30, size[0] - MARGIN, size[1] * 0.52)
        font, lines, line_h = fit_text(draw, slide.heading, brand, int(box[2] - box[0]), int(box[3] - box[1]), start_size=76, weight="bold")
        draw_multiline_centered(draw, lines, font, box, text_color, line_h)

        follow_font = get_font(brand, "bold", 42)
        follow_text = f"Follow {handle_text} for more"
        w = draw.textlength(follow_text, font=follow_font)
        draw.text(((size[0] - w) / 2, size[1] * 0.58), follow_text, font=follow_font, fill=text_color)

        if slide.body:
            body_font = get_font(brand, "regular", 32)
            body_lines = wrap_text(draw, slide.body, body_font, size[0] - 2 * MARGIN)
            draw_multiline_centered(
                draw, body_lines, body_font,
                (MARGIN, size[1] * 0.64, size[0] - MARGIN, size[1] * 0.76),
                text_color, 42,
            )
    else:
        accent = hex_to_rgb(brand.accent_color)
        draw_badge(draw, brand, (MARGIN + 34, MARGIN + 90), index + 1, accent, readable_text_color(brand.accent_color))

        heading_box = (MARGIN, size[1] * 0.20, size[0] - MARGIN, size[1] * 0.42)
        font, lines, line_h = fit_text(draw, slide.heading, brand, int(heading_box[2] - heading_box[0]), int(heading_box[3] - heading_box[1]), start_size=64, weight="bold")
        draw_multiline_centered(draw, lines, font, heading_box, text_color, line_h, align="left")

        if slide.body:
            body_box = (MARGIN, size[1] * 0.46, size[0] - MARGIN, size[1] * 0.80)
            body_font, body_lines, body_line_h = fit_text(draw, slide.body, brand, int(body_box[2] - body_box[0]), int(body_box[3] - body_box[1]), start_size=42, min_size=26, weight="regular")
            y = body_box[1]
            for line in body_lines:
                draw.text((body_box[0], y), line, font=body_font, fill=text_color)
                y += body_line_h

        draw.rectangle([0, size[1] - 14, size[0], size[1]], fill=accent)

    dot_bg = brand.primary_color if is_hook else brand.accent_color if is_cta else brand.background_color
    draw_page_dots(
        draw, size, index, total,
        active=readable_text_color(dot_bg),
        inactive=mix(text_color, hex_to_rgb(dot_bg), 0.6),
    )
    draw_handle(draw, brand, size, text_color)
    return canvas


TEMPLATES = {
    "quote": {"render": render_quote_slide, "size": SQUARE_SIZE, "multi_slide": False},
    "stat": {"render": render_stat_slide, "size": SQUARE_SIZE, "multi_slide": False},
    "list_carousel": {"render": render_carousel_slide, "size": PORTRAIT_SIZE, "multi_slide": True},
}


def render_post(brand: Brand, slides: list[Slide], template: str) -> list[Image.Image]:
    spec = TEMPLATES.get(template, TEMPLATES["list_carousel"])
    size = spec["size"]
    if spec["multi_slide"]:
        total = len(slides)
        return [spec["render"](brand, s, i, total, size) for i, s in enumerate(slides)]
    return [spec["render"](brand, slides[0], size)]


def save_slides(brand_id: str, images: list[Image.Image], post_slug: str) -> list[str]:
    paths = []
    for i, img in enumerate(images):
        path = new_post_slide_path(brand_id, post_slug, i)
        img.save(path, "PNG")
        paths.append(str(path))
    return paths
