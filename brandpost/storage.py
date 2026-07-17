"""Per-brand file storage: logos, custom fonts, and generated post images."""

from __future__ import annotations

import shutil
from pathlib import Path

from slugify import slugify

from brandpost.config import BRANDS_DIR, STATIC_BRANDS_DIR, STATIC_DIR


def brand_dir(brand_id: str) -> Path:
    d = BRANDS_DIR / brand_id
    (d / "assets").mkdir(parents=True, exist_ok=True)
    (d / "library").mkdir(parents=True, exist_ok=True)
    return d


def assets_dir(brand_id: str) -> Path:
    return brand_dir(brand_id) / "assets"


def posts_dir(brand_id: str) -> Path:
    """Rendered post images. Lives under static/, not data/, so they can be
    served at a public URL (see config.STATIC_DIR)."""
    d = STATIC_BRANDS_DIR / brand_id / "posts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_public_path(local_path: str) -> str:
    """Return a path under STATIC_DIR usable with public_url_for.

    Posts rendered before post images moved from data/ to static/ still have
    slide_paths pointing at the old data/brands/<id>/posts/ location, which
    isn't publicly served. Copy the file into static/ on demand instead of
    failing, so old posts keep working without needing to be regenerated."""
    p = Path(local_path).resolve()
    try:
        p.relative_to(STATIC_DIR.resolve())
        return str(p)
    except ValueError:
        pass

    if not p.exists():
        raise FileNotFoundError(
            f"Rendered image not found at {local_path} - regenerate this post from Generate Post."
        )
    brand_id = p.parent.parent.name  # .../<brand_id>/posts/<filename>
    dest = STATIC_BRANDS_DIR / brand_id / "posts" / p.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy(p, dest)
    return str(dest)


def public_url_for(local_path: str, base_url: str) -> str:
    """Convert a rendered post's local file path to the public URL Streamlit's
    static file server exposes it at (requires server.enableStaticServing)."""
    public_path = ensure_public_path(local_path)
    rel = Path(public_path).relative_to(STATIC_DIR.resolve())
    return f"{base_url.rstrip('/')}/app/static/{rel.as_posix()}"


def library_dir(brand_id: str) -> Path:
    return brand_dir(brand_id) / "library"


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


def save_library_image(brand_id: str, uploaded_file) -> str:
    """Save a brand photo (product/lifestyle shot) to use as post backgrounds."""
    ext = uploaded_file.name.split(".")[-1].lower()
    existing = list_library_images(brand_id)
    dest = library_dir(brand_id) / f"img_{len(existing) + 1:03d}.{ext}"
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


def save_library_image_from_bytes(brand_id: str, data: bytes, ext: str = "jpg") -> str:
    """Save image bytes (e.g. a downloaded Adobe Stock thumbnail) into the brand library."""
    existing = list_library_images(brand_id)
    dest = library_dir(brand_id) / f"img_{len(existing) + 1:03d}.{ext}"
    with open(dest, "wb") as f:
        f.write(data)
    return str(dest)


def list_library_images(brand_id: str) -> list[str]:
    return sorted(str(p) for p in library_dir(brand_id).glob("img_*"))


def delete_library_image(path: str) -> None:
    p = Path(path)
    if p.exists():
        p.unlink()
