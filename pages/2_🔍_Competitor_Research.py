import streamlit as st

from brandpost import competitor_analysis, db
from brandpost.ui_common import require_brand

st.set_page_config(page_title="Competitor Research — BrandPost Studio", page_icon="🔍", layout="wide")
db.init_db()
brand = require_brand()

st.title("🔍 Competitor Research")
st.caption(
    "Add competitor Instagram accounts. The app pulls their public posts and "
    "distills what's driving engagement — feed this straight into content research."
)

with st.form("add_competitor", clear_on_submit=True):
    raw = st.text_input(
        "Competitor Instagram profile URL or @username",
        placeholder="https://www.instagram.com/someaccount or @someaccount",
    )
    add = st.form_submit_button("Add competitor")
if add and raw.strip():
    username = competitor_analysis.extract_username(raw)
    db.add_competitor(brand.id, username, f"https://www.instagram.com/{username}/")
    st.success(f"Added @{username}.")
    st.rerun()

st.divider()

competitors = db.list_competitors(brand.id)
if not competitors:
    st.info("No competitors added yet.")
else:
    for comp in competitors:
        with st.expander(f"@{comp.username}" + (f"  ·  last analyzed {comp.last_analyzed}" if comp.last_analyzed else "  ·  not analyzed yet"), expanded=False):
            c1, c2, c3 = st.columns([1, 1, 3])
            if c1.button("Analyze from Instagram", key=f"analyze_{comp.id}"):
                with st.spinner(f"Fetching public posts for @{comp.username}..."):
                    try:
                        n = competitor_analysis.analyze_and_store(brand.id, comp.id, comp.username)
                        st.success(f"Pulled {n} posts from @{comp.username}.")
                        st.rerun()
                    except competitor_analysis.ScrapeUnavailable as exc:
                        st.warning(str(exc))
            if c2.button("Remove competitor", key=f"remove_{comp.id}"):
                db.delete_competitor(comp.id)
                st.rerun()

            st.markdown("**Add a post manually** (use this if live scraping is blocked)")
            with st.form(f"manual_post_{comp.id}", clear_on_submit=True):
                caption = st.text_area("Caption (include hashtags)", key=f"cap_{comp.id}")
                mc1, mc2, mc3 = st.columns(3)
                likes = mc1.number_input("Likes", min_value=0, value=0, key=f"likes_{comp.id}")
                comments = mc2.number_input("Comments", min_value=0, value=0, key=f"comments_{comp.id}")
                is_carousel = mc3.checkbox("Carousel post", key=f"carousel_{comp.id}")
                submit_manual = st.form_submit_button("Add post")
            if submit_manual and caption.strip():
                competitor_analysis.add_manual_post(
                    brand.id, comp.id, caption, likes=int(likes), comments=int(comments), is_carousel=is_carousel
                )
                st.success("Post added.")
                st.rerun()

st.divider()
st.subheader("Aggregate insights")
insights = competitor_analysis.compute_insights(brand.id)
if not insights:
    st.caption("Analyze at least one competitor (or add posts manually) to see insights here.")
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Posts analyzed", insights.post_count)
    m2.metric("Avg. likes", f"{insights.avg_likes:.0f}")
    m3.metric("Avg. comments", f"{insights.avg_comments:.0f}")
    m4.metric("Carousel share", f"{insights.carousel_share:.0%}")

    st.markdown("**Most-used hashtags across competitors**")
    st.write(" ".join(f"`#{tag}` ({count})" for tag, count in insights.top_hashtags))

    st.markdown("**Top performing competitor posts**")
    for p in insights.top_posts:
        st.markdown(f"- ❤️ {p.likes} · 💬 {p.comments} — {p.caption[:220]}{'…' if len(p.caption) > 220 else ''}")
