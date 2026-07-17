"""Uploads rendered post images to Cloudinary so they have a stable public
HTTPS URL for Buffer to fetch (Buffer has no upload endpoint of its own -
see buffer_api.py). Uses the official `cloudinary` SDK for signed uploads
so signature generation is handled correctly rather than hand-rolled.
"""

from __future__ import annotations


class CloudinaryError(RuntimeError):
    pass


def is_configured(cloud_name: str | None, api_key: str | None, api_secret: str | None) -> bool:
    return bool(cloud_name and api_key and api_secret)


def upload_image(local_path: str, cloud_name: str, api_key: str, api_secret: str) -> str:
    """Upload a local image and return its permanent secure_url."""
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:  # pragma: no cover
        raise CloudinaryError("the cloudinary package is not installed") from exc

    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True)
    try:
        result = cloudinary.uploader.upload(local_path, folder="brandpost_studio")
    except Exception as exc:
        raise CloudinaryError(f"Cloudinary upload failed: {exc}") from exc

    url = result.get("secure_url")
    if not url:
        raise CloudinaryError(f"Cloudinary returned no secure_url - unexpected response: {result}")
    return url
