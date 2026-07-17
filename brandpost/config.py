"""Paths and constants shared across the app."""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
BRANDS_DIR = DATA_DIR / "brands"
DB_PATH = DATA_DIR / "brandpost.db"

# Rendered post images live under static/ (not data/) so Streamlit's static file
# serving (server.enableStaticServing) can expose them at a public URL for
# scheduling APIs like Buffer, which require a stable public image URL and have
# no upload endpoint of their own.
STATIC_DIR = ROOT_DIR / "static"
STATIC_BRANDS_DIR = STATIC_DIR / "brands"

DATA_DIR.mkdir(parents=True, exist_ok=True)
BRANDS_DIR.mkdir(parents=True, exist_ok=True)
STATIC_BRANDS_DIR.mkdir(parents=True, exist_ok=True)

# Post canvas sizes (Instagram-safe)
SQUARE_SIZE = (1080, 1080)
PORTRAIT_SIZE = (1080, 1350)

DEFAULT_LLM_MODEL = "claude-sonnet-5"

SYSTEM_FONT_FALLBACKS = {
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "italic": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    ],
    "serif_bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    ],
}
