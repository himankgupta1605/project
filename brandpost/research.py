"""Turns a brand profile + competitor insights into concrete content ideas."""

from __future__ import annotations

from brandpost import llm
from brandpost.competitor_analysis import CompetitorInsights
from brandpost.models import Brand, ContentIdea

SYSTEM_PROMPT = """You are a senior Instagram content strategist who specialises in
organic-growth-driven content for brands. You design content that is highly
researched, non-generic, and genuinely useful or entertaining to the target
audience, following formats proven to drive saves, shares and follows
(carousels with real value, strong hooks, pattern interrupts, myth-busting,
data-backed tips, relatable stories)."""


def _format_insights(insights: CompetitorInsights | None) -> str:
    if not insights:
        return "No competitor data available yet."
    top_tags = ", ".join(f"#{t}" for t, _ in insights.top_hashtags[:10])
    sample_captions = "\n".join(
        f"- ({p.likes} likes) {p.caption[:180]}" for p in insights.top_posts
    )
    return f"""Competitor benchmark (from {insights.post_count} analyzed posts):
- Average likes: {insights.avg_likes:.0f}, average comments: {insights.avg_comments:.0f}
- Carousel share: {insights.carousel_share:.0%}
- Average caption length: {insights.avg_caption_length} characters
- Frequently used hashtags: {top_tags}
- Their best performing captions:
{sample_captions}"""


def generate_content_ideas(
    brand: Brand,
    insights: CompetitorInsights | None,
    count: int = 10,
    api_key: str | None = None,
) -> list[ContentIdea]:
    prompt = f"""Brand: {brand.name}
Niche: {brand.niche}
Brand voice / tone: {brand.tone}
Target audience: {brand.audience}

{_format_insights(insights)}

Generate {count} distinct Instagram content ideas for this brand's daily posting
plan. Spread them across a healthy mix of content pillars (e.g. education,
myth-busting, behind-the-scenes, social proof, trends, listicle tips,
inspiration/relatable). Each idea should be specific enough to write a caption
and design a post from immediately - not vague.

Return a JSON array where each item has exactly these keys:
"pillar" (short category name), "topic" (specific idea title), "angle"
(1-2 sentences on the unique hook/angle to take), "hashtags" (array of 8-12
relevant hashtags, no # symbol, lowercase, mix of broad and niche)."""

    raw = llm.generate_json(prompt, system=SYSTEM_PROMPT, api_key=api_key, max_tokens=3000)
    ideas: list[ContentIdea] = []
    for item in raw:
        hashtags = item.get("hashtags", [])
        if isinstance(hashtags, list):
            hashtags = " ".join(f"#{h.lstrip('#')}" for h in hashtags)
        ideas.append(
            ContentIdea(
                id=None,
                brand_id=brand.id,
                pillar=item.get("pillar", ""),
                topic=item.get("topic", ""),
                angle=item.get("angle", ""),
                hashtags=hashtags,
                source="llm",
                created_at="",
            )
        )
    return ideas
