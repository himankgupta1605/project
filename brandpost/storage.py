"""Per-brand file storage: logos, custom fonts, and generated post images."""

from __future__ import annotations

from pathlib import Path

from slugify import slugify

from brandpost.config import BRANDS_DIR


def brand_dir(brand_id: str) -> Path:
    d = BRANDS_DIR / brand_id
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "posts").mkdir(parents=True, exist_ok=True)
    return d


def assets_dir(brand_id: str) -> Path:
    return brand_dir(brand_id) / "assets"


def posts_dir(brand_id: str) -> Path:
    return brand_dir(brand_id) / "posts"


def make_brand_id(name: str) -> str:
    base = slugify(name) or "brand"
    candidate = base
    i = 2
    while (BRANDS_DIR / candidate).exists():
        candidate = f"{base}-{i}"
        i += 1
    return candidate


def save_uploaded_file(brand_id: str, uploaded_file, filename: str) -> str:
    """uploaded_file: a Streamlit UploadedFile (has .getbuffer())."""
    dest = assets_dir(brand_id) / filename
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def new_post_slide_path(brand_id: str, post_slug: str, index: int) -> Path:
    return posts_dir(brand_id) / f"{post_slug}_{index:02d}.png"
