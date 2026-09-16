# Unfinished

A personal essay blog. Markdown in, static HTML out, no framework.

## Write a post

Create `posts/<slug>.md`. The slug becomes the URL (`/posts/<slug>/`).

```
title: The Fights I Want to Choose
date: 2026-09-15
summary: One sentence for the archive list and the feed.
---

Body starts here, in plain markdown.
```

Standalone pages work the same way in `pages/` and need only a `title`.

## Build and preview

```sh
uv run --with markdown python build.py
python3 -m http.server -d dist 8000
```

Then open http://localhost:8000.

## Before publishing

Set `base_url` in `build.py` to the real domain. It is what the Atom feed and share
previews point at, and on a GitHub Pages project site its path also becomes the site
root that every link is written against.

## Deploy

`.github/workflows/deploy.yml` builds `dist/` and publishes it to GitHub Pages on every
push to `main`. Enable it under Settings > Pages > Source > GitHub Actions.

Netlify, Vercel, and Cloudflare Pages all work too: build command
`uv run --with markdown python build.py`, publish directory `dist`.
