"""Generates the Instagram caption plus the on-image slide copy for a post."""

from __future__ import annotations

from dataclasses import dataclass, field

from brandpost import llm
from brandpost.models import Brand, ContentIdea

SYSTEM_PROMPT = """You are an expert Instagram copywriter and content designer for
brands optimizing for organic growth (saves, shares, comments, follows). You
write scroll-stopping hooks, concise high-value body copy suitable for
on-image text (short lines, no fluff), and captions that extend the value of
the post and end with a natural call to action. You always match the given
brand voice exactly."""


@dataclass
class Slide:
    heading: str
    body: str = ""


@dataclass
class PostContent:
    caption: str
    hashtags: list[str]
    slides: list[Slide]
    suggested_template: str = "list_carousel"


def generate_post_content(
    brand: Brand,
    idea: ContentIdea,
    post_type: str = "carousel",
    slide_count: int = 6,
    api_key: str | None = None,
) -> PostContent:
    slide_guidance = (
        f"Produce exactly {slide_count} slides: slide 1 is a scroll-stopping hook/title "
        "(heading only, short), the middle slides each deliver one concrete point "
        "(short heading + 1-2 sentence body), and the final slide is a clear call to "
        "action (e.g. follow/save/share prompt tied to the brand)."
        if post_type == "carousel"
        else "Produce exactly 1 slide: a punchy heading (the core message, e.g. a quote, "
        "stat, or single tip) and a short supporting body line."
    )

    prompt = f"""Brand: {brand.name}
Niche: {brand.niche}
Brand voice / tone: {brand.tone}
Target audience: {brand.audience}
Instagram handle: {brand.handle or "(not set)"}

Content idea:
- Pillar: {idea.pillar}
- Topic: {idea.topic}
- Angle: {idea.angle}

Write the content for a {post_type} Instagram post about this idea.
{slide_guidance}

Also write the Instagram caption (separate from the on-image text): a strong
hook line, 2-4 short paragraphs expanding on the value with line breaks, and a
call to action. Keep on-image text short (it must fit on a 1080px square
image) - put the detail in the caption instead.

Suggest one template name that fits best: "quote", "stat", or "list_carousel".

Return JSON with exactly these keys: "caption" (string), "hashtags" (array of
8-15 lowercase strings, no # symbol), "slides" (array of objects with "heading"
and "body" strings, body may be empty for the hook slide), "suggested_template"
(one of quote/stat/list_carousel)."""

    raw = llm.generate_json(prompt, system=SYSTEM_PROMPT, api_key=api_key, max_tokens=2500)
    slides = [Slide(heading=s.get("heading", ""), body=s.get("body", "")) for s in raw.get("slides", [])]
    return PostContent(
        caption=raw.get("caption", ""),
        hashtags=[h.lstrip("#") for h in raw.get("hashtags", [])],
        slides=slides or [Slide(heading=idea.topic, body=idea.angle)],
        suggested_template=raw.get("suggested_template", "list_carousel"),
    )
