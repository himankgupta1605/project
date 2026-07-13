"""Resolve brand fonts for Pillow rendering, with safe system fallbacks."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

from brandpost.config import SYSTEM_FONT_FALLBACKS
from brandpost.models import Brand


def _first_existing(paths: list[str]) -> str | None:
    for p in paths:
        if p and Path(p).exists():
            return p
    return None


def resolve_font_path(brand: Brand, weight: str = "regular") -> str:
    """weight: 'regular', 'bold', 'italic', or 'serif_bold' (used for pull-quotes)."""
    if weight == "bold" and brand.font_bold_path and Path(brand.font_bold_path).exists():
        return brand.font_bold_path
    if weight == "regular" and brand.font_regular_path and Path(brand.font_regular_path).exists():
        return brand.font_regular_path
    fallback = _first_existing(SYSTEM_FONT_FALLBACKS.get(weight, SYSTEM_FONT_FALLBACKS["regular"]))
    if fallback:
        return fallback
    # last resort: any regular fallback
    return _first_existing(SYSTEM_FONT_FALLBACKS["regular"])


@lru_cache(maxsize=256)
def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def get_font(brand: Brand, weight: str = "regular", size: int = 40) -> ImageFont.FreeTypeFont:
    path = resolve_font_path(brand, weight)
    if not path:
        return ImageFont.load_default()
    return _load_font(path, size)
