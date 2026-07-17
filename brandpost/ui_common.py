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

    adobe_key = st.sidebar.text_input(
        "Adobe Stock API key (optional)",
        type="password",
        value=st.session_state.get("adobe_api_key", os.environ.get("ADOBE_STOCK_API_KEY", "")),
        help="Used to search Adobe Stock for post background photos on the Brand Setup page. "
        "Stored only for this session, never saved to disk.",
    )
    st.session_state["adobe_api_key"] = adobe_key

    buffer_key = st.sidebar.text_input(
        "Buffer API key (optional)",
        type="password",
        value=st.session_state.get("buffer_api_key", os.environ.get("BUFFER_API_KEY", "")),
        help="Used to schedule/publish rendered posts to Instagram via Buffer on the Library page. "
        "Stored only for this session, never saved to disk.",
    )
    st.session_state["buffer_api_key"] = buffer_key

    public_base_url = st.sidebar.text_input(
        "App public URL (for Buffer)",
        value=st.session_state.get("public_base_url", os.environ.get("PUBLIC_BASE_URL", "")),
        help="This app's own public HTTPS URL (e.g. https://yourapp.example.com), used to build "
        "public links to rendered post images — Buffer has no image upload endpoint and requires "
        "a stable public URL for each image. Leave blank if you're not scheduling via Buffer yet.",
        placeholder="https://yourapp.example.com",
    )
    st.session_state["public_base_url"] = public_base_url

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


def get_adobe_api_key() -> str | None:
    return st.session_state.get("adobe_api_key") or os.environ.get("ADOBE_STOCK_API_KEY")


def get_buffer_api_key() -> str | None:
    return st.session_state.get("buffer_api_key") or os.environ.get("BUFFER_API_KEY")


def get_public_base_url() -> str | None:
    return st.session_state.get("public_base_url") or os.environ.get("PUBLIC_BASE_URL")
