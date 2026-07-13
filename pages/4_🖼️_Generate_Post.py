from slugify import slugify

import streamlit as st

from brandpost import caption_generator, db, image_templates
from brandpost.caption_generator import Slide
from brandpost.models import ContentIdea, Post
from brandpost.ui_common import require_api_key, require_brand

st.set_page_config(page_title="Generate Post — BrandPost Studio", page_icon="🖼️", layout="wide")
db.init_db()
brand = require_brand()

st.title("🖼️ Generate Post")

ideas = db.list_content_ideas(brand.id)
idea_options = {f"[{i.pillar}] {i.topic}": i for i in ideas}

st.subheader("1. Pick a content idea")
preselected_id = st.session_state.pop("selected_idea_id", None)
use_manual = st.checkbox("Write a custom idea instead of using the research backlog", value=not ideas)

if use_manual:
    pillar = st.text_input("Pillar", value="Custom")
    topic = st.text_input("Topic", placeholder="e.g. 5 morning habits that changed my skin")
    angle = st.text_area("Angle / hook", placeholder="What makes this specific and non-generic?")
    idea = ContentIdea(id=None, brand_id=brand.id, pillar=pillar, topic=topic, angle=angle, hashtags="", source="manual", created_at="")
else:
    labels = list(idea_options.keys())
    default_index = 0
    if preselected_id:
        for i, obj in enumerate(idea_options.values()):
            if obj.id == preselected_id:
                default_index = i
                break
    chosen_label = st.selectbox("Idea", labels, index=default_index)
    idea = idea_options[chosen_label]
    st.caption(idea.angle)

st.subheader("2. Choose format")
c1, c2, c3 = st.columns(3)
post_type = c1.selectbox("Post type", ["carousel", "static"])
if post_type == "carousel":
    template = c2.selectbox("Template", ["list_carousel"], index=0)
    slide_count = c3.slider("Slides", 3, 8, 6)
else:
    template = c2.selectbox("Template", ["quote", "stat"], index=0)
    slide_count = 1

if st.button("Generate caption + copy", type="primary"):
    if not idea.topic:
        st.error("Give the idea a topic first.")
        st.stop()
    api_key = require_api_key()
    with st.spinner("Writing on-brand copy..."):
        try:
            content = caption_generator.generate_post_content(
                brand, idea, post_type=post_type, slide_count=slide_count, api_key=api_key
            )
            st.session_state["draft_content"] = content
            st.session_state["draft_topic"] = idea.topic
        except caption_generator.llm.LLMNotConfigured as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Generation failed: {exc}")

draft: caption_generator.PostContent | None = st.session_state.get("draft_content")

if draft:
    st.divider()
    st.subheader("3. Review & edit")

    caption_text = st.text_area("Caption", value=draft.caption, height=200)
    hashtags_text = st.text_input("Hashtags (space separated)", value=" ".join(f"#{h}" for h in draft.hashtags))

    st.markdown("**On-image slide copy**")
    edited_slides = []
    for i, slide in enumerate(draft.slides):
        with st.expander(f"Slide {i + 1}: {slide.heading[:40]}", expanded=(i == 0)):
            heading = st.text_input("Heading", value=slide.heading, key=f"slide_h_{i}")
            body = st.text_area("Body", value=slide.body, key=f"slide_b_{i}")
            edited_slides.append(Slide(heading=heading, body=body))

    render_template = "list_carousel"
    if post_type == "static":
        suggested = draft.suggested_template if draft.suggested_template in ("quote", "stat") else template
        render_template = st.selectbox(
            "Template for rendering", ["quote", "stat"],
            index=["quote", "stat"].index(suggested),
        )

    if st.button("Render images", type="primary"):
        with st.spinner("Rendering..."):
            images = image_templates.render_post(brand, edited_slides, render_template)
            slug = slugify(st.session_state.get("draft_topic", "post"))[:40] or "post"
            paths = image_templates.save_slides(brand.id, images, slug)
            post = db.add_post(
                Post(
                    id=None, brand_id=brand.id, post_type=post_type, template=render_template,
                    topic=st.session_state.get("draft_topic", ""), caption=caption_text,
                    hashtags=hashtags_text, slide_paths=paths, created_at="",
                )
            )
            st.session_state.pop("draft_content", None)
            st.success("Post rendered and saved to the Library.")

        cols = st.columns(min(len(paths), 4) or 1)
        for i, p in enumerate(paths):
            with cols[i % len(cols)]:
                st.image(p, use_container_width=True)
                with open(p, "rb") as f:
                    st.download_button("Download", f.read(), file_name=p.split("/")[-1], mime="image/png", key=f"dl_{i}")
