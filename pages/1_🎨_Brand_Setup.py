import streamlit as st

from brandpost import db, storage
from brandpost.models import Brand
from brandpost.ui_common import render_sidebar

st.set_page_config(page_title="Brand Setup — BrandPost Studio", page_icon="🎨", layout="wide")
db.init_db()
current_brand = render_sidebar()

st.title("🎨 Brand Setup")
st.caption("Define the identity every post for this brand will be generated from.")

brands = db.list_brands()
mode = st.radio(
    "Mode",
    ["Create new brand", "Edit existing brand"] if brands else ["Create new brand"],
    horizontal=True,
)

editing: Brand | None = None
if mode == "Edit existing brand":
    names = [b.name for b in brands]
    pick = st.selectbox("Brand to edit", names, index=names.index(current_brand.name) if current_brand else 0)
    editing = brands[names.index(pick)]

with st.form("brand_form", clear_on_submit=False):
    st.subheader("Identity")
    col1, col2 = st.columns(2)
    name = col1.text_input("Brand name", value=editing.name if editing else "")
    handle = col2.text_input("Instagram handle (without @)", value=editing.handle if editing else "")
    niche = st.text_input(
        "Niche / industry", value=editing.niche if editing else "",
        placeholder="e.g. sustainable skincare for sensitive skin",
    )
    tone = st.text_area(
        "Brand voice & tone", value=editing.tone if editing else "",
        placeholder="e.g. warm, expert, encouraging, a little playful, never salesy",
    )
    audience = st.text_area(
        "Target audience", value=editing.audience if editing else "",
        placeholder="e.g. eco-conscious women 25-40 who want visible results without harsh chemicals",
    )
    website = st.text_input("Website (optional)", value=editing.website if editing else "")

    st.subheader("Color theme")
    c1, c2, c3, c4, c5 = st.columns(5)
    primary_color = c1.color_picker("Primary", editing.primary_color if editing else "#111827")
    secondary_color = c2.color_picker("Secondary", editing.secondary_color if editing else "#F9FAFB")
    accent_color = c3.color_picker("Accent", editing.accent_color if editing else "#6366F1")
    background_color = c4.color_picker("Background", editing.background_color if editing else "#FFFFFF")
    text_color = c5.color_picker("Text", editing.text_color if editing else "#111827")

    st.subheader("Assets (optional — falls back to clean system fonts if omitted)")
    a1, a2, a3 = st.columns(3)
    logo_file = a1.file_uploader("Logo (PNG, transparent background recommended)", type=["png"])
    font_regular_file = a2.file_uploader("Regular font (.ttf/.otf)", type=["ttf", "otf"])
    font_bold_file = a3.file_uploader("Bold font (.ttf/.otf)", type=["ttf", "otf"])

    submitted = st.form_submit_button("Save brand", type="primary")

if submitted:
    if not name.strip():
        st.error("Brand name is required.")
        st.stop()

    brand_id = editing.id if editing else storage.make_brand_id(name)
    storage.brand_dir(brand_id)

    logo_path = editing.logo_path if editing else None
    font_regular_path = editing.font_regular_path if editing else None
    font_bold_path = editing.font_bold_path if editing else None

    if logo_file is not None:
        logo_path = storage.save_uploaded_file(brand_id, logo_file, "logo.png")
    if font_regular_file is not None:
        ext = font_regular_file.name.split(".")[-1]
        font_regular_path = storage.save_uploaded_file(brand_id, font_regular_file, f"font_regular.{ext}")
    if font_bold_file is not None:
        ext = font_bold_file.name.split(".")[-1]
        font_bold_path = storage.save_uploaded_file(brand_id, font_bold_file, f"font_bold.{ext}")

    brand = Brand(
        id=brand_id,
        name=name.strip(),
        niche=niche.strip(),
        tone=tone.strip(),
        audience=audience.strip(),
        primary_color=primary_color,
        secondary_color=secondary_color,
        accent_color=accent_color,
        background_color=background_color,
        text_color=text_color,
        font_regular_path=font_regular_path,
        font_bold_path=font_bold_path,
        logo_path=logo_path,
        handle=handle.strip(),
        website=website.strip(),
        created_at=editing.created_at if editing else db.now(),
    )
    db.upsert_brand(brand)
    st.session_state["brand_id"] = brand_id
    st.success(f"Saved brand '{brand.name}'.")
    st.rerun()

st.divider()
st.subheader("All brands")
if not brands:
    st.caption("No brands yet.")
else:
    for b in brands:
        with st.expander(f"{b.name}  ·  {b.niche or 'no niche set'}"):
            cols = st.columns([1, 1, 1, 1, 1, 2])
            for col, (label, color) in zip(
                cols,
                [
                    ("Primary", b.primary_color), ("Secondary", b.secondary_color),
                    ("Accent", b.accent_color), ("Background", b.background_color),
                    ("Text", b.text_color),
                ],
            ):
                col.markdown(
                    f"<div style='width:100%;height:28px;border-radius:6px;background:{color};"
                    f"border:1px solid #0002'></div><div style='font-size:11px;text-align:center'>{label}</div>",
                    unsafe_allow_html=True,
                )
            if b.logo_path:
                st.image(b.logo_path, width=80)
            if st.button("Delete this brand", key=f"delete_{b.id}"):
                db.delete_brand(b.id)
                st.success(f"Deleted {b.name}.")
                st.rerun()
