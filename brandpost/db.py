"""SQLite persistence layer. No ORM — small helpers over sqlite3."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

from brandpost.config import DB_PATH
from brandpost.models import Brand, Competitor, CompetitorPost, ContentIdea, Post

SCHEMA = """
CREATE TABLE IF NOT EXISTS brands (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    niche TEXT,
    tone TEXT,
    audience TEXT,
    primary_color TEXT,
    secondary_color TEXT,
    accent_color TEXT,
    background_color TEXT,
    text_color TEXT,
    font_regular_path TEXT,
    font_bold_path TEXT,
    logo_path TEXT,
    handle TEXT,
    website TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    url TEXT,
    last_analyzed TEXT
);

CREATE TABLE IF NOT EXISTS competitor_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_id INTEGER NOT NULL REFERENCES competitors(id) ON DELETE CASCADE,
    shortcode TEXT,
    caption TEXT,
    hashtags TEXT,
    likes INTEGER,
    comments INTEGER,
    is_video INTEGER,
    is_carousel INTEGER,
    post_date TEXT,
    url TEXT
);

CREATE TABLE IF NOT EXISTS content_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    pillar TEXT,
    topic TEXT,
    angle TEXT,
    hashtags TEXT,
    source TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    post_type TEXT,
    template TEXT,
    topic TEXT,
    caption TEXT,
    hashtags TEXT,
    slide_paths TEXT,
    created_at TEXT
);
"""


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- brands --

def upsert_brand(brand: Brand) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO brands (id, name, niche, tone, audience, primary_color,
                secondary_color, accent_color, background_color, text_color,
                font_regular_path, font_bold_path, logo_path, handle, website, created_at)
            VALUES (:id, :name, :niche, :tone, :audience, :primary_color,
                :secondary_color, :accent_color, :background_color, :text_color,
                :font_regular_path, :font_bold_path, :logo_path, :handle, :website, :created_at)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, niche=excluded.niche, tone=excluded.tone,
                audience=excluded.audience, primary_color=excluded.primary_color,
                secondary_color=excluded.secondary_color, accent_color=excluded.accent_color,
                background_color=excluded.background_color, text_color=excluded.text_color,
                font_regular_path=excluded.font_regular_path, font_bold_path=excluded.font_bold_path,
                logo_path=excluded.logo_path, handle=excluded.handle, website=excluded.website
            """,
            brand.as_dict(),
        )


def list_brands() -> list[Brand]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM brands ORDER BY name").fetchall()
        return [Brand(**dict(r)) for r in rows]


def get_brand(brand_id: str) -> Optional[Brand]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM brands WHERE id = ?", (brand_id,)).fetchone()
        return Brand(**dict(row)) if row else None


def delete_brand(brand_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))


# ----------------------------------------------------------- competitors --

def add_competitor(brand_id: str, username: str, url: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO competitors (brand_id, username, url, last_analyzed) VALUES (?, ?, ?, NULL)",
            (brand_id, username, url),
        )
        return cur.lastrowid


def list_competitors(brand_id: str) -> list[Competitor]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM competitors WHERE brand_id = ? ORDER BY id", (brand_id,)
        ).fetchall()
        return [Competitor(**dict(r)) for r in rows]


def delete_competitor(competitor_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM competitors WHERE id = ?", (competitor_id,))


def mark_competitor_analyzed(competitor_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE competitors SET last_analyzed = ? WHERE id = ?", (now(), competitor_id)
        )


def replace_competitor_posts(competitor_id: int, posts: list[CompetitorPost]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM competitor_posts WHERE competitor_id = ?", (competitor_id,))
        conn.executemany(
            """
            INSERT INTO competitor_posts
                (competitor_id, shortcode, caption, hashtags, likes, comments,
                 is_video, is_carousel, post_date, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p.competitor_id, p.shortcode, p.caption, p.hashtags, p.likes,
                    p.comments, int(p.is_video), int(p.is_carousel), p.post_date, p.url,
                )
                for p in posts
            ],
        )


def list_competitor_posts(brand_id: str) -> list[CompetitorPost]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT cp.* FROM competitor_posts cp
            JOIN competitors c ON c.id = cp.competitor_id
            WHERE c.brand_id = ?
            ORDER BY cp.likes DESC
            """,
            (brand_id,),
        ).fetchall()
        return [
            CompetitorPost(
                id=r["id"], competitor_id=r["competitor_id"], shortcode=r["shortcode"],
                caption=r["caption"], hashtags=r["hashtags"], likes=r["likes"],
                comments=r["comments"], is_video=bool(r["is_video"]),
                is_carousel=bool(r["is_carousel"]), post_date=r["post_date"], url=r["url"],
            )
            for r in rows
        ]


# --------------------------------------------------------- content ideas --

def add_content_idea(idea: ContentIdea) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO content_ideas (brand_id, pillar, topic, angle, hashtags, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (idea.brand_id, idea.pillar, idea.topic, idea.angle, idea.hashtags,
             idea.source, idea.created_at or now()),
        )
        return cur.lastrowid


def list_content_ideas(brand_id: str) -> list[ContentIdea]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM content_ideas WHERE brand_id = ? ORDER BY id DESC", (brand_id,)
        ).fetchall()
        return [ContentIdea(**dict(r)) for r in rows]


def clear_content_ideas(brand_id: str) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM content_ideas WHERE brand_id = ?", (brand_id,))


def get_content_idea(idea_id: int) -> Optional[ContentIdea]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM content_ideas WHERE id = ?", (idea_id,)).fetchone()
        return ContentIdea(**dict(row)) if row else None


# ------------------------------------------------------------------ posts --

def add_post(post: Post) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (brand_id, post_type, template, topic, caption, hashtags,
                slide_paths, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (post.brand_id, post.post_type, post.template, post.topic, post.caption,
             post.hashtags, json.dumps(post.slide_paths), post.created_at or now()),
        )
        return cur.lastrowid


def list_posts(brand_id: str) -> list[Post]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM posts WHERE brand_id = ? ORDER BY id DESC", (brand_id,)
        ).fetchall()
        posts = []
        for r in rows:
            d = dict(r)
            d["slide_paths"] = json.loads(d["slide_paths"] or "[]")
            posts.append(Post(**d))
        return posts


def delete_post(post_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
