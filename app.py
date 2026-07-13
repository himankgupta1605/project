import streamlit as st

from brandpost import competitor_analysis, db
from brandpost.ui_common import render_sidebar

st.set_page_config(page_title="BrandPost Studio", page_icon="📸", layout="wide")

db.init_db()
brand = render_sidebar()

st.title("📸 BrandPost Studio")
st.caption(
    "A single customizable engine for generating on-brand, well-researched, "
    "high-quality Instagram posts — static and carousel — for any number of brands."
)

st.markdown(
    """
### How it works
1. **Brand Setup** — define a brand once: colors, fonts, logo, voice, and audience.
2. **Competitor Research** — feed in competitor Instagram profiles; the app pulls
   their public posts and summarizes what's working (hashtags, engagement, formats).
3. **Content Research** — turns the brand profile + competitor insights into a
   backlog of concrete, on-brand content ideas.
4. **Generate Post** — pick an idea, generate caption + on-image copy, and render
   a fully branded static post or carousel.
5. **Library** — browse and download everything you've generated for a brand.

Every brand gets its own color theme, fonts, logo, research, and content — the
underlying app and templates stay identical.
"""
)

if brand:
    st.divider()
    st.subheader(f"Overview — {brand.name}")
    competitors = db.list_competitors(brand.id)
    ideas = db.list_content_ideas(brand.id)
    posts = db.list_posts(brand.id)
    insights = competitor_analysis.compute_insights(brand.id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Competitors tracked", len(competitors))
    c2.metric("Competitor posts analyzed", insights.post_count if insights else 0)
    c3.metric("Content ideas ready", len(ideas))
    c4.metric("Posts generated", len(posts))

    if not competitors:
        st.info("Next step: add a few competitor Instagram accounts on the **Competitor Research** page.")
    elif not ideas:
        st.info("Next step: generate content ideas on the **Content Research** page.")
    elif not posts:
        st.info("Next step: turn an idea into a post on the **Generate Post** page.")
else:
    st.info("Start by creating your first brand on the **Brand Setup** page (see sidebar).")
