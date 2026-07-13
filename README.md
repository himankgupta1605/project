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
   brand's colors, fonts, and logo.
5. **Library** — browse, preview, and download everything generated for a
   brand.

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or paste it into the sidebar at runtime
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
  image_templates.py         Pillow rendering engine (quote / stat / carousel
                              templates), themed entirely from the Brand object
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
