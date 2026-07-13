"""Adobe Stock search integration used to source background photos.

Uses Adobe Stock's public Search API (API-key auth, no OAuth needed for
search). Results are preview-resolution thumbnails, not licensed final-use
assets - fine for drafting a post's look, but the brand should license the
image through Adobe Stock before publishing anything commercially, or use
their own uploaded photos via the manual library instead.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

SEARCH_URL = "https://stock.adobe.io/Rest/Media/1/Search/Files"
PRODUCT_HEADER = "BrandPostStudio/1.0"


class AdobeStockError(RuntimeError):
    pass


def _api_key(explicit_key: str | None = None) -> str | None:
    return explicit_key or os.environ.get("ADOBE_STOCK_API_KEY")


def is_configured(explicit_key: str | None = None) -> bool:
    return bool(_api_key(explicit_key))


@dataclass
class StockPhoto:
    id: str
    title: str
    thumbnail_url: str


def search_photos(query: str, api_key: str | None = None, limit: int = 12) -> list[StockPhoto]:
    key = _api_key(api_key)
    if not key:
        raise AdobeStockError(
            "No Adobe Stock API key found. Set ADOBE_STOCK_API_KEY or enter a key in the sidebar."
        )
    try:
        import requests
    except ImportError as exc:  # pragma: no cover
        raise AdobeStockError("the requests library is not installed") from exc

    params = {
        "search_parameters[words]": query,
        "search_parameters[limit]": limit,
        "search_parameters[filters][content_type:photo]": 1,
        "result_columns[]": ["id", "title", "thumbnail_500_url"],
    }
    headers = {"x-api-key": key, "x-product": PRODUCT_HEADER}
    try:
        resp = requests.get(SEARCH_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        raise AdobeStockError(f"Adobe Stock search failed: {exc}") from exc

    data = resp.json()
    return [
        StockPhoto(id=str(f.get("id")), title=f.get("title", ""), thumbnail_url=f.get("thumbnail_500_url", ""))
        for f in data.get("files", [])
        if f.get("thumbnail_500_url")
    ]


def fetch_image_bytes(url: str) -> bytes:
    import requests

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.content
