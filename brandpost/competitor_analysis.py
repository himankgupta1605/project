"""Competitor Instagram analysis.

Instagram aggressively rate-limits and often blocks anonymous scraping, so
this module is best-effort: it tries a public-data fetch via `instaloader`
and reports a clear, catchable error when Instagram refuses the request
(rather than crashing the app). Callers should let users fall back to
pasting caption/hashtag data manually when live scraping isn't available.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from brandpost import db
from brandpost.models import CompetitorPost

HASHTAG_RE = re.compile(r"#(\w+)")
USERNAME_FROM_URL_RE = re.compile(r"instagram\.com/([A-Za-z0-9_.]+)")


class ScrapeUnavailable(RuntimeError):
    """Raised when Instagram can't be reached or refuses anonymous access."""


def extract_username(text: str) -> str:
    text = text.strip()
    match = USERNAME_FROM_URL_RE.search(text)
    if match:
        return match.group(1).strip("/")
    return text.lstrip("@").strip("/")


def fetch_competitor_posts(username: str, max_posts: int = 12) -> list[CompetitorPost]:
    """Fetch recent public posts for a competitor. Raises ScrapeUnavailable on failure."""
    try:
        import instaloader
    except ImportError as exc:  # pragma: no cover
        raise ScrapeUnavailable("instaloader is not installed") from exc

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        posts = []
        for i, p in enumerate(profile.get_posts()):
            if i >= max_posts:
                break
            caption = p.caption or ""
            posts.append(
                CompetitorPost(
                    id=None,
                    competitor_id=-1,  # filled in by caller
                    shortcode=p.shortcode,
                    caption=caption,
                    hashtags=" ".join(HASHTAG_RE.findall(caption)),
                    likes=p.likes or 0,
                    comments=p.comments or 0,
                    is_video=p.is_video,
                    is_carousel=p.typename == "GraphSidecar",
                    post_date=p.date_utc.isoformat(),
                    url=f"https://www.instagram.com/p/{p.shortcode}/",
                )
            )
        return posts
    except Exception as exc:
        raise ScrapeUnavailable(
            f"Could not fetch @{username} from Instagram ({exc}). "
            "Instagram frequently blocks anonymous scraping — you can add posts "
            "manually instead."
        ) from exc


def analyze_and_store(brand_id: str, competitor_id: int, username: str, max_posts: int = 12) -> int:
    posts = fetch_competitor_posts(username, max_posts=max_posts)
    for p in posts:
        p.competitor_id = competitor_id
    db.replace_competitor_posts(competitor_id, posts)
    db.mark_competitor_analyzed(competitor_id)
    return len(posts)


def add_manual_post(
    brand_id: str,
    competitor_id: int,
    caption: str,
    likes: int = 0,
    comments: int = 0,
    is_carousel: bool = False,
) -> None:
    existing = [p for p in db.list_competitor_posts(brand_id) if p.competitor_id == competitor_id]
    post = CompetitorPost(
        id=None,
        competitor_id=competitor_id,
        shortcode=f"manual-{len(existing) + 1}",
        caption=caption,
        hashtags=" ".join(HASHTAG_RE.findall(caption)),
        likes=likes,
        comments=comments,
        is_video=False,
        is_carousel=is_carousel,
        post_date="",
        url="",
    )
    db.replace_competitor_posts(competitor_id, existing + [post])
    db.mark_competitor_analyzed(competitor_id)


@dataclass
class CompetitorInsights:
    post_count: int
    avg_likes: float
    avg_comments: float
    carousel_share: float
    avg_caption_length: int
    top_hashtags: list[tuple[str, int]]
    top_posts: list[CompetitorPost]


def compute_insights(brand_id: str, top_n: int = 5) -> CompetitorInsights | None:
    posts = db.list_competitor_posts(brand_id)
    if not posts:
        return None

    hashtag_counter = Counter()
    for p in posts:
        hashtag_counter.update(tag.lower() for tag in p.hashtags.split() if tag)

    n = len(posts)
    return CompetitorInsights(
        post_count=n,
        avg_likes=sum(p.likes for p in posts) / n,
        avg_comments=sum(p.comments for p in posts) / n,
        carousel_share=sum(1 for p in posts if p.is_carousel) / n,
        avg_caption_length=int(sum(len(p.caption) for p in posts) / n),
        top_hashtags=hashtag_counter.most_common(15),
        top_posts=sorted(posts, key=lambda p: p.likes, reverse=True)[:top_n],
    )
