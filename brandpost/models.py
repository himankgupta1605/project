"""Typed data structures used across the app."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Brand:
    id: str
    name: str
    niche: str = ""
    tone: str = ""
    audience: str = ""
    primary_color: str = "#111827"
    secondary_color: str = "#F9FAFB"
    accent_color: str = "#6366F1"
    background_color: str = "#FFFFFF"
    text_color: str = "#111827"
    font_regular_path: Optional[str] = None
    font_bold_path: Optional[str] = None
    logo_path: Optional[str] = None
    handle: str = ""
    website: str = ""
    created_at: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Competitor:
    id: Optional[int]
    brand_id: str
    username: str
    url: str
    last_analyzed: Optional[str] = None


@dataclass
class CompetitorPost:
    id: Optional[int]
    competitor_id: int
    shortcode: str
    caption: str
    hashtags: str
    likes: int
    comments: int
    is_video: bool
    is_carousel: bool
    post_date: str
    url: str


@dataclass
class ContentIdea:
    id: Optional[int]
    brand_id: str
    pillar: str
    topic: str
    angle: str
    hashtags: str
    source: str
    created_at: str


@dataclass
class Post:
    id: Optional[int]
    brand_id: str
    post_type: str  # "static" or "carousel"
    template: str
    topic: str
    caption: str
    hashtags: str
    slide_paths: list = field(default_factory=list)
    created_at: str = ""
