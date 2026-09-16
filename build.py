"""Render the markdown in posts/ and pages/ into a static site under dist/."""

import html
import math
import os
import shutil
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from string import Template
from urllib.parse import urlparse

import markdown

ROOT = Path(__file__).parent
POSTS_DIR = ROOT / "posts"
PAGES_DIR = ROOT / "pages"
STATIC_DIR = ROOT / "static"
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "dist"

FRONTMATTER_SEPARATOR = "---"
WORDS_PER_MINUTE = 220


@dataclass(frozen=True)
class Site:
    title: str
    tagline: str
    author: str
    base_url: str

    @property
    def root_path(self) -> str:
        return urlparse(self.base_url).path.rstrip("/")


SITE = Site(
    title="Unfinished",
    tagline="Thinking out loud while I am still in the middle of it.",
    author="Ananya Joshi",
    base_url=os.environ.get("SITE_BASE_URL", "https://ananyajoshi0203-cpu.github.io/unfinished"),
)


@dataclass(frozen=True)
class Document:
    slug: str
    title: str
    summary: str
    published_on: date | None
    body_markdown: str

    @property
    def display_date(self) -> str:
        if self.published_on is None:
            return ""
        return f"{self.published_on:%B} {self.published_on.day}, {self.published_on:%Y}"

    @property
    def iso_date(self) -> str:
        return self.published_on.isoformat() if self.published_on else ""

    @property
    def reading_time(self) -> str:
        minutes = max(1, math.ceil(len(self.body_markdown.split()) / WORDS_PER_MINUTE))
        return f"{minutes} min read"


def parse_document(path: Path) -> Document:
    frontmatter_text, _, body = path.read_text().partition(f"\n{FRONTMATTER_SEPARATOR}\n")
    fields = dict(
        (key.strip(), value.strip())
        for key, _, value in (line.partition(":") for line in frontmatter_text.splitlines() if line.strip())
    )
    published = fields.get("date")
    return Document(
        slug=path.stem,
        title=fields.get("title", path.stem),
        summary=fields.get("summary", ""),
        published_on=date.fromisoformat(published) if published else None,
        body_markdown=body.strip(),
    )


def load(directory: Path) -> list[Document]:
    return [parse_document(path) for path in sorted(directory.glob("*.md"))]


def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=["smarty"], output_format="html")


def template(name: str) -> Template:
    return Template((TEMPLATE_DIR / f"{name}.html").read_text())


def wrap(content: str, *, page_title: str, description: str, og_type: str) -> str:
    return template("base").substitute(
        page_title=html.escape(page_title),
        description=html.escape(description),
        og_type=og_type,
        site_title=html.escape(SITE.title),
        author=html.escape(SITE.author),
        root=SITE.root_path,
        content=content,
    )


def write(relative_path: str, document_html: str) -> None:
    destination = OUTPUT_DIR / relative_path / "index.html" if relative_path else OUTPUT_DIR / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document_html)


def render_index(posts: Sequence[Document]) -> str:
    entry = template("archive_entry")
    entries = "\n".join(
        entry.substitute(
            root=SITE.root_path,
            slug=post.slug,
            title=html.escape(post.title),
            summary=html.escape(post.summary),
            iso_date=post.iso_date,
            display_date=post.display_date,
        )
        for post in posts
    )
    body = template("index").substitute(tagline=html.escape(SITE.tagline), entries=entries)
    return wrap(body, page_title=SITE.title, description=SITE.tagline, og_type="website")


def render_post(post: Document) -> str:
    body = template("post").substitute(
        root=SITE.root_path,
        title=html.escape(post.title),
        iso_date=post.iso_date,
        display_date=post.display_date,
        reading_time=post.reading_time,
        body=render_markdown(post.body_markdown),
    )
    return wrap(
        body,
        page_title=f"{post.title} — {SITE.title}",
        description=post.summary,
        og_type="article",
    )


def render_page(page: Document) -> str:
    body = template("page").substitute(
        title=html.escape(page.title),
        body=render_markdown(page.body_markdown),
    )
    return wrap(
        body,
        page_title=f"{page.title} — {SITE.title}",
        description=page.summary or SITE.tagline,
        og_type="website",
    )


def render_feed(posts: Iterable[Document]) -> str:
    updated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    entries = "\n".join(
        f"""  <entry>
    <title>{html.escape(post.title)}</title>
    <link href="{SITE.base_url}/posts/{post.slug}/"/>
    <id>{SITE.base_url}/posts/{post.slug}/</id>
    <updated>{post.iso_date}T00:00:00Z</updated>
    <summary>{html.escape(post.summary)}</summary>
  </entry>"""
        for post in posts
        if post.published_on
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{html.escape(SITE.title)}</title>
  <subtitle>{html.escape(SITE.tagline)}</subtitle>
  <link href="{SITE.base_url}/feed.xml" rel="self"/>
  <link href="{SITE.base_url}/"/>
  <id>{SITE.base_url}/</id>
  <updated>{updated}</updated>
  <author><name>{html.escape(SITE.author)}</name></author>
{entries}
</feed>
"""


def build() -> None:
    posts = sorted(load(POSTS_DIR), key=lambda post: post.published_on or date.min, reverse=True)
    pages = load(PAGES_DIR)

    shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True)

    write("", render_index(posts))
    for post in posts:
        write(f"posts/{post.slug}", render_post(post))
    for page in pages:
        write(page.slug, render_page(page))

    (OUTPUT_DIR / "feed.xml").write_text(render_feed(posts))
    (OUTPUT_DIR / ".nojekyll").touch()
    for asset in STATIC_DIR.iterdir():
        shutil.copy2(asset, OUTPUT_DIR / asset.name)

    print(f"built {len(posts)} post(s) and {len(pages)} page(s) into {OUTPUT_DIR}")


if __name__ == "__main__":
    build()
