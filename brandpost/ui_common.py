"""Shared Streamlit sidebar / session-state helpers used by every page."""

from __future__ import annotations

import os

import streamlit as st

from brandpost import db
from brandpost.models import Brand


def render_sidebar() -> Brand | None:
    st.sidebar.title("BrandPost Studio")
    st.sidebar.caption("One interface. Infinite on-brand Instagram content.")

    api_key = st.sidebar.text_input(
        "Anthropic API key",
        type="password",
        value=st.session_state.get("api_key", os.environ.get("ANTHROPIC_API_KEY", "")),
        help="Used for competitor-informed research and copywriting. "
        "Stored only for this session, never saved to disk.",
    )
    st.session_state["api_key"] = api_key

    brands = db.list_brands()
    if not brands:
        st.sidebar.info("No brands yet — create one on the Brand Setup page.")
        st.session_state["brand_id"] = None
        return None

    names = [b.name for b in brands]
    ids = [b.id for b in brands]
    current_id = st.session_state.get("brand_id")
    default_index = ids.index(current_id) if current_id in ids else 0

    selected_name = st.sidebar.selectbox("Active brand", names, index=default_index)
    selected = brands[names.index(selected_name)]
    st.session_state["brand_id"] = selected.id

    with st.sidebar.expander("Brand palette", expanded=False):
        cols = st.columns(5)
        swatches = [
            ("Primary", selected.primary_color),
            ("Secondary", selected.secondary_color),
            ("Accent", selected.accent_color),
            ("Background", selected.background_color),
            ("Text", selected.text_color),
        ]
        for col, (label, color) in zip(cols, swatches):
            col.markdown(
                f"<div style='width:100%;height:32px;border-radius:6px;"
                f"background:{color};border:1px solid #0002' title='{label} {color}'></div>",
                unsafe_allow_html=True,
            )

    return selected


def require_brand() -> Brand:
    brand = render_sidebar()
    if brand is None:
        st.warning("Create a brand first on the **Brand Setup** page.")
        st.stop()
    return brand


def require_api_key() -> str:
    key = st.session_state.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        st.warning("Enter an Anthropic API key in the sidebar to use AI-generated research and copy.")
        st.stop()
    return key
