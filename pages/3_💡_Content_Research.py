import streamlit as st

from brandpost import competitor_analysis, db, research
from brandpost.ui_common import require_api_key, require_brand

st.set_page_config(page_title="Content Research — BrandPost Studio", page_icon="💡", layout="wide")
db.init_db()
brand = require_brand()

st.title("💡 Content Research")
st.caption(
    "Generates a backlog of concrete, on-brand post ideas from the brand profile "
    "plus whatever competitor insight is available."
)

insights = competitor_analysis.compute_insights(brand.id)
if insights:
    st.success(f"Using insights from {insights.post_count} analyzed competitor posts.")
else:
    st.info("No competitor data yet — ideas will be based on the brand profile only. "
             "Add competitors on the Competitor Research page for sharper, benchmarked ideas.")

col1, col2 = st.columns([1, 3])
count = col1.slider("Ideas to generate", 3, 20, 10)
generate = col1.button("Generate content ideas", type="primary")

if generate:
    api_key = require_api_key()
    with st.spinner("Researching content ideas..."):
        try:
            ideas = research.generate_content_ideas(brand, insights, count=count, api_key=api_key)
            for idea in ideas:
                db.add_content_idea(idea)
            st.success(f"Generated {len(ideas)} ideas.")
            st.rerun()
        except research.llm.LLMNotConfigured as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Generation failed: {exc}")

st.divider()

existing = db.list_content_ideas(brand.id)
if not existing:
    st.caption("No ideas yet — generate some above.")
else:
    if st.button("Clear all ideas"):
        db.clear_content_ideas(brand.id)
        st.rerun()

    for idea in existing:
        with st.expander(f"[{idea.pillar}] {idea.topic}"):
            st.write(idea.angle)
            st.caption(idea.hashtags)
            if st.button("Use this idea →", key=f"use_{idea.id}"):
                st.session_state["selected_idea_id"] = idea.id
                st.switch_page("pages/4_🖼️_Generate_Post.py")
