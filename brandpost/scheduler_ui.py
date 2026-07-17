"""Library page widget: schedule a rendered post to Instagram via Buffer."""

from __future__ import annotations

from datetime import datetime, time

import streamlit as st

from brandpost import buffer_api, cloudinary_host, db, storage
from brandpost.models import Brand, Post
from brandpost.ui_common import get_buffer_api_key, get_cloudinary_config, get_public_base_url


def _load_channels(api_key: str) -> list[buffer_api.Channel]:
    if "buffer_channels" not in st.session_state:
        try:
            st.session_state["buffer_channels"] = buffer_api.get_instagram_channels(api_key)
        except buffer_api.BufferError as exc:
            st.session_state["buffer_channels"] = []
            st.error(str(exc))
    return st.session_state["buffer_channels"]


def _public_image_urls(slide_paths: list[str], base_url: str | None) -> list[str]:
    """Get a public URL per slide, preferring Cloudinary when configured since it
    doesn't depend on the app's own deployment supporting static file serving."""
    cloud_config = get_cloudinary_config()
    cache = st.session_state.setdefault("cloudinary_uploads", {})
    urls = []
    for path in slide_paths:
        if cloud_config:
            if path not in cache:
                cache[path] = cloudinary_host.upload_image(path, *cloud_config)
            urls.append(cache[path])
        else:
            urls.append(storage.public_url_for(path, base_url))
    return urls


def render_scheduler(post: Post, brand: Brand) -> None:
    st.markdown("**Schedule to Instagram via Buffer**")

    if post.buffer_post_id:
        st.success(f"Scheduled via Buffer for {post.scheduled_at} (Buffer post `{post.buffer_post_id}`).")
        st.caption("Manage or reschedule this post from your Buffer dashboard.")
        return

    api_key = get_buffer_api_key()
    cloud_config = get_cloudinary_config()
    base_url = get_public_base_url()
    if not api_key:
        st.caption("Enter a Buffer API key in the sidebar to schedule this post.")
        return
    if not cloud_config and not base_url:
        st.caption(
            "Set up image hosting in the sidebar (\"Image hosting for Buffer\" — Cloudinary "
            "recommended) so Buffer can fetch the rendered images. Buffer has no image upload "
            "endpoint of its own."
        )
        return

    if post.post_type == "carousel" and len(post.slide_paths) > 1:
        st.caption(
            "⚠️ Multi-image carousel scheduling isn't explicitly documented by Buffer's API — "
            "verify the first scheduled carousel in your Buffer dashboard before relying on it."
        )

    if st.button("Load Instagram channels", key=f"load_channels_{post.id}"):
        st.session_state.pop("buffer_channels", None)
        _load_channels(api_key)

    channels = _load_channels(api_key)
    if not channels:
        st.caption("No Instagram channels found yet — click \"Load Instagram channels\" above.")
        return

    labels = [c.display_name or c.id for c in channels]
    channel_label = st.selectbox("Instagram channel", labels, key=f"channel_{post.id}")
    channel = channels[labels.index(channel_label)]

    queue_mode = st.checkbox(
        "Add to Buffer's next open queue slot instead of a specific time", value=False, key=f"queue_{post.id}"
    )
    scheduled_dt = None
    if not queue_mode:
        col1, col2 = st.columns(2)
        sched_date = col1.date_input("Scheduled date (UTC)", key=f"date_{post.id}")
        sched_time = col2.time_input("Scheduled time (UTC)", value=time(12, 0), key=f"time_{post.id}")
        scheduled_dt = datetime.combine(sched_date, sched_time)

    if st.button("Schedule post", type="primary", key=f"schedule_{post.id}"):
        try:
            with st.spinner("Uploading images..." if cloud_config else "Preparing images..."):
                image_urls = _public_image_urls(post.slide_paths, base_url)
            with st.spinner("Scheduling via Buffer..."):
                buffer_post_id = buffer_api.schedule_post(
                    api_key=api_key,
                    channel_id=channel.id,
                    caption=f"{post.caption}\n\n{post.hashtags}".strip(),
                    image_urls=image_urls,
                    scheduled_at=scheduled_dt,
                )
            scheduled_label = scheduled_dt.isoformat() + "Z" if scheduled_dt else "next queue slot"
            db.mark_post_scheduled(post.id, buffer_post_id, scheduled_label)
            st.success("Scheduled via Buffer.")
            st.rerun()
        except buffer_api.BufferError as exc:
            st.error(str(exc))
        except cloudinary_host.CloudinaryError as exc:
            st.error(str(exc))
        except (OSError, ValueError) as exc:
            st.error(f"Couldn't prepare images for scheduling: {exc}")
