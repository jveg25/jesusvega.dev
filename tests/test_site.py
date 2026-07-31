"""Checks that catch the ways this site can break silently.

It's a static site with no build step, so there's no compiler to tell you when
something is wrong. These tests stand in for one. They deliberately cover
failures a browser won't announce — a missing translation, a logo that 404s,
private data creeping back in from the CV — rather than restating what the
markup obviously says.

    uv run pytest
"""

from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "404.html"]


@pytest.fixture(scope="module")
def html() -> str:
    return (ROOT / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ── bilingual integrity ──────────────────────────────────────────────────
# The whole translation mechanism is "put both languages in the markup and let
# CSS hide one". Its failure mode is silent: forget the Spanish half and that
# content simply vanishes for Spanish readers, with no error anywhere.


def test_every_translated_element_has_its_counterpart(soup: BeautifulSoup):
    """Within any parent, lang="en" and lang="es" children must be balanced."""
    offenders = []

    for parent in soup.body.find_all(True):
        children = [c for c in parent.find_all(True, recursive=False) if c.get("lang")]
        if not children:
            continue

        en = sum(1 for c in children if c["lang"] == "en")
        es = sum(1 for c in children if c["lang"] == "es")
        if en != es:
            snippet = " ".join(parent.get_text(" ", strip=True).split())[:70]
            offenders.append(f"<{parent.name} class={parent.get('class')}>: "
                             f"{en} en / {es} es — {snippet!r}")

    assert not offenders, "Unbalanced translations:\n  " + "\n  ".join(offenders)


def test_only_supported_languages_are_used(soup: BeautifulSoup):
    used = {el["lang"] for el in soup.body.find_all(attrs={"lang": True})}
    assert used <= {"en", "es"}, f"Unexpected lang values: {used - {'en', 'es'}}"


def test_body_starts_in_a_real_language(soup: BeautifulSoup):
    """Set in the markup, not by script, so the page works before JS runs."""
    assert soup.body.get("data-lang") in {"en", "es"}


# ── privacy ──────────────────────────────────────────────────────────────
# The source CV carries a national ID and a phone number. Neither belongs on a
# public page, and both are easy to reintroduce by pasting from the CV again.


@pytest.mark.parametrize("page", PAGES)
def test_no_private_identifiers(page: str):
    text = (ROOT / page).read_text(encoding="utf-8")
    forbidden = {
        "DNI number": r"76534534",
        "phone number": r"999[\s-]?449[\s-]?254",
        "any Peruvian mobile": r"\+51[\s-]?9\d{2}[\s-]?\d{3}[\s-]?\d{3}",
    }
    for label, pattern in forbidden.items():
        assert not re.search(pattern, text), f"{label} found in {page}"


# ── content readiness ────────────────────────────────────────────────────


@pytest.mark.parametrize("page", PAGES)
def test_no_placeholder_text_survives(page: str):
    text = (ROOT / page).read_text(encoding="utf-8")
    for marker in ("[Placeholder]", "YOUR-USERNAME", "Lorem ipsum", "TODO", "FIXME"):
        assert marker not in text, f"{marker!r} still present in {page}"


def test_page_has_title_and_description(soup: BeautifulSoup):
    assert soup.title and soup.title.string.strip()
    desc = soup.find("meta", attrs={"name": "description"})
    assert desc and len(desc["content"]) > 50


# ── links and assets ─────────────────────────────────────────────────────


def _local_refs(soup: BeautifulSoup) -> list[str]:
    refs = []
    for tag, attr in (("img", "src"), ("script", "src"), ("link", "href")):
        for el in soup.find_all(tag):
            v = el.get(attr)
            if v and not urlparse(v).scheme and not v.startswith(("#", "//")):
                refs.append(v)
    # Logos are set as inline background-image, so they need finding separately.
    for el in soup.find_all(style=True):
        refs += re.findall(r"url\(([^)]+)\)", el["style"])
    return [r.strip("'\"") for r in refs]


@pytest.mark.parametrize("page", PAGES)
def test_referenced_files_exist(page: str):
    page_soup = BeautifulSoup((ROOT / page).read_text(encoding="utf-8"), "html.parser")
    missing = [r for r in _local_refs(page_soup) if not (ROOT / r.lstrip("/")).exists()]
    assert not missing, f"Referenced but not on disk ({page}): {missing}"


def test_external_links_use_https(soup: BeautifulSoup):
    bad = [
        a["href"] for a in soup.find_all("a", href=True)
        if urlparse(a["href"]).scheme not in ("", "https", "mailto")
    ]
    assert not bad, f"Non-HTTPS links: {bad}"


def test_every_tab_has_a_panel(soup: BeautifulSoup):
    tabs = {a["data-tab"] for a in soup.select(".tabs a[data-tab]")}
    panels = {s["id"] for s in soup.select("section.panel[id]")}
    assert tabs == panels, f"tabs={tabs} panels={panels}"


# ── accessibility ────────────────────────────────────────────────────────


@pytest.mark.parametrize("page", PAGES)
def test_images_have_alt_text(page: str):
    page_soup = BeautifulSoup((ROOT / page).read_text(encoding="utf-8"), "html.parser")
    missing = [i for i in page_soup.find_all("img") if i.get("alt") is None]
    assert not missing, f"<img> without alt in {page}: {missing}"


@pytest.mark.parametrize("page", PAGES)
def test_document_declares_a_language(page: str):
    page_soup = BeautifulSoup((ROOT / page).read_text(encoding="utf-8"), "html.parser")
    assert page_soup.html.get("lang")


def test_headings_start_at_h1_and_do_not_skip(soup: BeautifulSoup):
    levels = [int(h.name[1]) for h in soup.find_all(re.compile(r"^h[1-6]$"))]
    assert levels and levels[0] == 1, "page should open with an <h1>"
    for prev, cur in zip(levels, levels[1:]):
        assert cur <= prev + 1, f"heading jumps from h{prev} to h{cur}"


# ── deployment config ────────────────────────────────────────────────────
# _headers pins a sha256 of the inline JSON-LD block. Editing the JSON without
# updating the hash would make browsers refuse the structured data, which is
# exactly the kind of breakage nobody notices for months.


def test_csp_hash_matches_the_inline_json_ld(html: str):
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert block, "JSON-LD block not found"

    digest = base64.b64encode(hashlib.sha256(block.group(1).encode()).digest()).decode()
    expected = f"sha256-{digest}"

    headers = (ROOT / "_headers").read_text(encoding="utf-8")
    assert expected in headers, (
        f"CSP hash in _headers is stale.\n"
        f"Replace the sha256-… in script-src with:\n  {expected}"
    )


def test_json_ld_is_valid_json(html: str):
    import json
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    data = json.loads(block.group(1))
    assert data["@type"] == "Person" and data["name"]


def test_sitemap_and_robots_agree_on_the_domain():
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    assert "https://jesusvega.dev/" in sitemap
    assert "https://jesusvega.dev/sitemap.xml" in robots
