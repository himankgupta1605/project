import streamlit as st

from brandpost import db
from brandpost.ui_common import require_brand

st.set_page_config(page_title="Library — BrandPost Studio", page_icon="📚", layout="wide")
db.init_db()
brand = require_brand()

st.title("📚 Library")
st.caption(f"Everything generated for {brand.name}.")

posts = db.list_posts(brand.id)
if not posts:
    st.info("No posts yet — head to Generate Post to make your first one.")
    st.stop()

for post in posts:
    with st.expander(f"[{post.post_type}/{post.template}] {post.topic or '(untitled)'}  ·  {post.created_at}", expanded=False):
        cols = st.columns(min(len(post.slide_paths), 5) or 1)
        for i, path in enumerate(post.slide_paths):
            with cols[i % len(cols)]:
                st.image(path, use_container_width=True)
        st.markdown("**Caption**")
        st.write(post.caption)
        st.caption(post.hashtags)
        if st.button("Delete post", key=f"del_post_{post.id}"):
            db.delete_post(post.id)
            st.rerun()
