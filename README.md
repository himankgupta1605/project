# BrandPost Studio

A single, reusable engine for generating on-brand, well-researched, high-quality
Instagram content — static posts and carousels — for any number of brands. The
interface and logic stay identical across brands; only each brand's color
theme, fonts, logo, competitor research, and generated content differ.

## How it works

1. **Brand Setup** — define a brand once: name, niche, voice/tone, audience,
   a 5-color theme, logo, and optional custom fonts.
2. **Competitor Research** — add competitor Instagram accounts. The app tries
   to pull their public posts (captions, hashtags, likes/comments, carousel
   vs. static) via `instaloader`. Instagram aggressively blocks anonymous
   scraping, so a manual-entry fallback lets you paste in competitor post
   data by hand when live fetching is blocked — either path feeds the same
   aggregate insights (top hashtags, average engagement, carousel share,
   best-performing captions).
3. **Content Research** — an LLM (Claude, via the Anthropic API) turns the
   brand profile plus competitor insights into a backlog of specific,
   non-generic content ideas spread across content pillars.
4. **Generate Post** — pick an idea, generate an Instagram caption plus
   on-image slide copy in the brand's voice, review/edit it, then render a
   fully branded static post (quote or stat-card template) or carousel
   (hook → value slides → CTA) with Pillow — themed automatically from the
   brand's colors, fonts, and logo. Each slide can use a flat brand-color
   background (with subtle blurred accent-color shapes tucked into the
   corners for depth) or a brand photo with a dark scrim behind the text for
   more visually varied, creative posts. Captions never include a raw
   Instagram link — CTAs reference the handle only.
5. **Library** — browse, preview, and download everything generated for a
   brand.

## Photo backgrounds

Brand Setup has a **Photo library** section per brand, filled two ways:

- **Manual upload** — product/lifestyle photos you already have.
- **Adobe Stock search** — enter an Adobe Stock API key (sidebar, session-only,
  never saved to disk; or set `ADOBE_STOCK_API_KEY`) and search Adobe's photo
  library by keyword right from Brand Setup; picked results are saved into the
  same per-brand library. Search results are preview-resolution thumbnails for
  drafting a look — license the image through Adobe Stock before publishing a
  post commercially, or stick to your own uploaded photos for anything final.

Once a brand has library photos, Generate Post lets you assign one as the
background for any slide (or leave it solid-color) independently, per slide.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # or paste it into the sidebar at runtime
export ADOBE_STOCK_API_KEY=...           # optional — enables Adobe Stock photo search
streamlit run app.py
```

Data is stored locally: brand records, competitor data, and content ideas in
a SQLite database at `data/brandpost.db`; per-brand logos, fonts, and
generated post images under `data/brands/<brand-id>/`.

## Project layout

```
app.py                     Home page (multi-brand overview)
pages/                     Streamlit multipage UI (Brand Setup, Competitor
                            Research, Content Research, Generate Post, Library)
brandpost/
  config.py                Paths, canvas sizes, font fallbacks
  models.py                Brand / Competitor / ContentIdea / Post dataclasses
  db.py                    SQLite persistence
  storage.py                Per-brand file storage (logos, fonts, output images)
  fonts.py                  Brand font resolution with system fallbacks
  llm.py                    Anthropic API wrapper (text + JSON)
  competitor_analysis.py    Instagram scraping (instaloader) + manual fallback
                             + aggregate insight computation
  research.py                Brand + competitor insights -> content idea backlog
  caption_generator.py       Content idea -> caption + on-image slide copy
                              (strips any raw Instagram links from output)
  image_templates.py         Pillow rendering engine (quote / stat / carousel
                              templates, photo backgrounds with scrim, decorative
                              accent shapes), themed entirely from the Brand object
  adobe_stock.py              Adobe Stock photo search (API-key auth)
```

## Notes on Instagram scraping

Instagram returns 403s to unauthenticated/anonymous scraping in most
environments, `instaloader` included. `competitor_analysis.py` treats this as
an expected, catchable condition (`ScrapeUnavailable`) rather than a crash —
the UI surfaces the error and offers manual post entry as a first-class path,
not an afterthought. If you have infrastructure that supports authenticated
scraping (e.g. a logged-in `instaloader` session or a third-party Instagram
data API), swap it in behind `fetch_competitor_posts()`; nothing else in the
app needs to change.

## Extending to a new brand

No code changes are required. Create a new brand in **Brand Setup** with its
own colors/fonts/logo/voice, add its competitors, run research, and generate
posts — the same templates and pipeline automatically re-theme for it.
