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
SITE_BASE_URL=http://localhost:8000 uv run --with markdown python build.py
python3 -m http.server -d dist 8000
```

Then open http://localhost:8000. The override matters: the published site lives under
`/unfinished`, so a build without it writes links a local server cannot resolve.

## Deploy

Every push to `main` rebuilds and republishes
[the site](https://ananyajoshi0203-cpu.github.io/unfinished/) via
`.github/workflows/deploy.yml`.

`base_url` in `build.py` is what the Atom feed and link previews point at, and its path
is the root every link is written against. Change it if the site ever moves to a custom
domain, where the path is empty.
