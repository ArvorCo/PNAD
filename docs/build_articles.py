#!/usr/bin/env python3
"""Render the ``docs/artigo_*.md`` essays into styled long-read HTML pages.

The Markdown files stay the single source of truth: every ``artigo_*.html`` in
``docs/`` is generated from its ``.md`` sibling through one shared template
(:data:`PAGE`) and one shared stylesheet (``docs/assets/artigo.css``). Editing a
generated HTML by hand is pointless -- the next build overwrites it.

What the renderer derives from the Markdown itself, so nothing has to be
restated in the config:

* the ``<title>`` and the page headline come from the first ``# H1``;
* a lone ``## H2`` sitting directly under that H1 is treated as the deck
  (standfirst) and lifted out of the body into the masthead;
* the meta description is condensed from the deck, or from the first
  paragraph/blockquote when there is no deck;
* the table of contents is built from the top-level sections;
* word count and reading time are counted on the rendered text.

Essays whose Markdown uses repeated ``# H1`` for their parts (``artigo_pt`` and
``artigo_en``) get every heading demoted one level, so the page keeps exactly
one ``<h1>`` and the parts become ``<h2>`` -- the document outline the TOC and
screen readers expect. No prose is added, removed or reordered.

The build is idempotent: identical inputs produce byte-identical outputs (no
timestamps, no counters), so it is safe to run on every commit.

Usage::

    uv run --with markdown python3 docs/build_articles.py
    uv run --with markdown python3 docs/build_articles.py --output /tmp/preview
    uv run --with markdown python3 docs/build_articles.py --only artigo_pt --check
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

try:
    import markdown
except ModuleNotFoundError:  # pragma: no cover - guidance beats a traceback
    sys.exit(
        "error: the 'markdown' package is missing.\n"
        "Run this script the way the repo does:\n"
        "    uv run --with markdown python3 docs/build_articles.py"
    )

DOCS = Path(__file__).resolve().parent

SITE = "https://brasil.arvor.co"
OG_IMAGE = f"{SITE}/img/arvor_og.png"
WORDS_PER_MINUTE = 220
DESCRIPTION_LIMIT = 158


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Link:
    """A labelled hyperlink shown in the masthead."""

    href: str
    label: str


@dataclass(frozen=True)
class Article:
    """Everything that cannot be inferred from the Markdown source."""

    slug: str
    lang: str
    eyebrow: str
    #: Optional companion page (interactive essay, dossier) linked in the header.
    related: Link | None = None
    #: Slug of the same essay in the other language, for the PT/EN toggle.
    translation: str | None = None
    #: Short social-card headline; falls back to the H1.
    social_title: str | None = None
    #: Extra ``rel="alternate"`` hreflang entries are derived from `translation`.
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source(self) -> Path:
        return DOCS / f"{self.slug}.md"

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


ARTICLES: tuple[Article, ...] = (
    Article(
        slug="artigo_pt",
        lang="pt-BR",
        eyebrow="Ensaio · PNAD Contínua anual · visita 5",
        related=Link("pnad.html", "Ensaio interativo"),
        translation="artigo_en",
        social_title="O Brasil auditável: um retrato em quinze fotografias",
    ),
    Article(
        slug="artigo_en",
        lang="en",
        eyebrow="Essay · PNAD Contínua annual · visit 5",
        related=Link("pnad.html", "Interactive essay"),
        translation="artigo_pt",
        social_title="The auditable Brazil: a portrait in fifteen photographs",
    ),
    Article(
        slug="artigo_nexus_btg_150626",
        lang="pt-BR",
        eyebrow="Auditoria eleitoral · BTG/Nexus · 4ª rodada · 15/06/2026",
        related=Link("nexus_btg_150626.html", "Dossiê completo"),
        social_title="BTG/Nexus 15/06: o banco que mediu voto e vendeu narrativa",
    ),
    Article(
        slug="artigo_quaest_100626",
        lang="pt-BR",
        eyebrow="Auditoria eleitoral · Quaest/Genial · 10/06/2026",
        related=Link("quaest_100626.html", "Dossiê completo"),
        social_title="Os intergalácticos: a direita que vota em Lula com vergonha de dizer",
    ),
)


#: UI chrome, per language. Keys mirror the placeholders used in :data:`PAGE`.
STRINGS: dict[str, dict[str, str]] = {
    "pt-BR": {
        "skip": "Pular para o conteúdo",
        "home": "Todos os relatórios",
        "toc": "Sumário",
        "toc_aria": "Sumário do artigo",
        "reading": "min de leitura",
        "words": "palavras",
        "note": "Nota metodológica",
        "lang_label": "Idioma do artigo",
        "nav_aria": "Navegação do artigo",
        "foot": (
            "Análise independente construída sobre bases oficiais, documentos públicos "
            "e código aberto. Todo número citado é reproduzível a partir do repositório: "
            "a metodologia está documentada, os dados vêm do IBGE, do TSE e do Banco Central, "
            "e qualquer leitor pode refazer as contas e nos desmentir."
        ),
        "foot_home": "Biblioteca de relatórios",
        "foot_source": "Fonte deste artigo (Markdown)",
        "foot_repo": "Repositório",
    },
    "en": {
        "skip": "Skip to content",
        "home": "All reports",
        "toc": "Contents",
        "toc_aria": "Table of contents",
        "reading": "min read",
        "words": "words",
        "note": "Methodological note",
        "lang_label": "Article language",
        "nav_aria": "Article navigation",
        "foot": (
            "Independent analysis built on official statistics, public documents and open "
            "code. Every figure quoted is reproducible from the repository: the methodology "
            "is documented, the data comes from IBGE, TSE and the Central Bank, and any "
            "reader can redo the arithmetic and prove us wrong."
        ),
        "foot_home": "Report library",
        "foot_source": "Source of this article (Markdown)",
        "foot_repo": "Repository",
    },
}

#: Short language codes for the PT/EN toggle.
LANG_BADGE = {"pt-BR": "PT", "en": "EN"}

#: Numbers worth pulling out of the prose typographically. Locale-aware: the
#: decimal mark is a comma in pt-BR and a dot in en, so a rule written for one
#: locale would wrongly grab thousands separators in the other ("1.774
#: municípios", "1,774 municipalities"). Currency runs first so that
#: "R$ 3.444" is consumed whole before any decimal rule sees it.
#:
#: Scale words are ordered longest-first and closed with ``\b``: without both,
#: "R$ 1 milhão" matches the shorter "mil" alternative and the span is closed
#: mid-word, leaving a stray "hão" in the prose.
_PT_SCALE = r"(?:mil(?:hão|hões)|bil(?:hão|hões)|tril(?:hão|hões)|mil)\b"
_EN_SCALE = r"(?:thousand|million|billion|trillion)s?\b"

STAT_PATTERNS: dict[str, str] = {
    "pt-BR": "|".join(
        (
            rf"R\$\s?\d[\d.]*(?:,\d+)?(?:\s{_PT_SCALE})?",
            r"±\s?\d+(?:,\d+)?(?:\s?p\.p\.)?",
            r"\d+(?:,\d+)?\s?(?:por cento\b|%)",
            r"\d+,\d+(?:\s?(?:p\.p\.|SM\b))?",
        )
    ),
    "en": "|".join(
        (
            rf"R\$\s?\d[\d,]*(?:\.\d+)?(?:\s{_EN_SCALE})?",
            r"±\s?\d+(?:\.\d+)?(?:\s?pp\b)?",
            r"\d+(?:\.\d+)?\s?(?:per cent\b|percent\b|%)",
            r"\d+\.\d+(?:\s?(?:pp|MW)\b)?",
        )
    ),
}


# --------------------------------------------------------------------------- #
# markdown pre-processing
# --------------------------------------------------------------------------- #

HEADING_RE = re.compile(r"^(#{1,6})(\s+)(.*)$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def _iter_prose_lines(lines: list[str]):
    """Yield ``(index, line)`` for lines outside fenced code blocks."""
    in_fence = False
    for index, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield index, line


def split_source(text: str) -> tuple[str, str | None, str]:
    """Split raw Markdown into ``(title, deck, body)``.

    The title is the first H1. A single H2 immediately following it is treated
    as the deck *only* when the document has exactly one H1 -- in the PNAD
    essays every part is an H1, so their H2s are real sections, not decks.
    Both title and deck are removed from the body; nothing else is touched.
    """
    lines = text.splitlines()
    prose = list(_iter_prose_lines(lines))

    title_index = title = None
    for index, line in prose:
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) == 1:
            title_index, title = index, match.group(3).strip()
            break
    if title is None or title_index is None:
        raise ValueError("no level-1 heading found; cannot derive a title")

    rest = [(i, ln) for i, ln in prose if i > title_index]
    extra_h1 = any(
        (m := HEADING_RE.match(ln)) and len(m.group(1)) == 1 for _, ln in rest
    )

    drop = {title_index}
    deck = None
    if not extra_h1:
        for index, line in rest:
            if not line.strip():
                continue
            match = HEADING_RE.match(line)
            if match and len(match.group(1)) == 2:
                deck = match.group(3).strip()
                drop.add(index)
            break

    body_lines = [ln for i, ln in enumerate(lines) if i not in drop]
    body = "\n".join(body_lines).strip("\n")
    if extra_h1:
        body = demote_headings(body)
    return title, deck, body


def demote_headings(text: str) -> str:
    """Push every heading down one level, leaving the page a single ``<h1>``."""
    lines = text.splitlines()
    demoted = list(lines)
    for index, line in _iter_prose_lines(lines):
        match = HEADING_RE.match(line)
        if match and len(match.group(1)) < 6:
            demoted[index] = f"#{match.group(1)}{match.group(2)}{match.group(3)}"
    return "\n".join(demoted)


def slugify(value: str, separator: str = "-") -> str:
    """Accent-folding slugify: 'o país partido' -> 'o-pais-partido'.

    Markdown's built-in slugify drops non-ASCII letters outright, which turns
    'país' into 'pas'. Transliterating first keeps the anchors readable.
    """
    folded = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in folded if not unicodedata.combining(ch))
    ascii_text = ascii_text.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^\w\s-]", "", ascii_text).strip().lower()
    return re.sub(r"[\s_-]+", separator, ascii_text)


# --------------------------------------------------------------------------- #
# html post-processing
# --------------------------------------------------------------------------- #

TAG_RE = re.compile(r"<[^>]+>")
TAG_SPLIT_RE = re.compile(r"(<[^>]+>)")
H2_RE = re.compile(r'(<h2 id="[^"]*">)(.*?)(</h2>)', re.DOTALL)
BLOCKQUOTE_RE = re.compile(r"<blockquote>(.*?)</blockquote>", re.DOTALL)
TABLE_RE = re.compile(r"<table>.*?</table>", re.DOTALL)
PART_RE = re.compile(
    r"^\s*((?:parte|part)\s+\d+)\s*[—–-]\s*(.+)$", re.IGNORECASE | re.DOTALL
)
SKIP_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def strip_tags(fragment: str) -> str:
    """Plain text of an HTML fragment, whitespace collapsed."""
    text = TAG_RE.sub(" ", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def count_words(fragment: str) -> int:
    """Words in the visible text of an HTML fragment (URLs live in attributes)."""
    return len(re.findall(r"[^\W_][\w'’‐-―-]*", strip_tags(fragment), re.UNICODE))


def mark_stats(body: str, lang: str) -> str:
    """Wrap statistical figures in ``<span class="stat">`` for a mono treatment.

    Only text nodes are touched -- the HTML is split on tags first, so URLs and
    attribute values can never be rewritten. Headings are skipped: mono digits
    inside a Fraunces display line look like a typo, not a decision.
    """
    pattern = re.compile(STAT_PATTERNS[lang])
    out: list[str] = []
    skip_depth = 0
    for token in TAG_SPLIT_RE.split(body):
        if token.startswith("<"):
            name = token.lstrip("</").split(" ", 1)[0].rstrip(">/").lower()
            if name in SKIP_TAGS:
                skip_depth += -1 if token.startswith("</") else 1
                skip_depth = max(skip_depth, 0)
            out.append(token)
        elif token and skip_depth == 0:
            out.append(
                pattern.sub(lambda m: f'<span class="stat">{m.group(0)}</span>', token)
            )
        else:
            out.append(token)
    return "".join(out)


def mark_lede(body: str) -> str:
    """Tag the first top-level paragraph as the drop-cap opener.

    'Top-level' matters: the PNAD essays open with a blockquote (the
    methodological note), and a drop cap belongs on the first paragraph of the
    prose, not inside the note.
    """
    depth = 0
    for match in TAG_SPLIT_RE.finditer(body):
        token = match.group(0)
        name = token.lstrip("</").split(" ", 1)[0].rstrip(">/").lower()
        if name in ("blockquote", "table", "ul", "ol", "aside"):
            depth += -1 if token.startswith("</") else 1
            depth = max(depth, 0)
        elif name == "p" and depth == 0 and not token.startswith("</"):
            start, end = match.span()
            return f'{body[:start]}<p class="lede">{body[end:]}'
    return body


def label_note(body: str, label: str) -> str:
    """Give the first blockquote the 'ficha técnica' label."""
    match = BLOCKQUOTE_RE.search(body)
    if not match:
        return body
    inner = match.group(1)
    labelled = f'<blockquote><p class="ficha-label">{html.escape(label)}</p>{inner}</blockquote>'
    return body[: match.start()] + labelled + body[match.end() :]


def format_parts(body: str) -> str:
    """Split 'parte 1 — o país partido ao meio' into an eyebrow and a title.

    Purely typographic: the two spans hold exactly the words the Markdown had,
    minus the em dash that separated them.
    """

    def repl(match: re.Match[str]) -> str:
        open_tag, inner, close_tag = match.groups()
        part = PART_RE.match(inner)
        if not part:
            return match.group(0)
        number, title = part.group(1).strip(), part.group(2).strip()
        return (
            f'{open_tag}<span class="part-no">{number}</span>'
            f'<span class="part-title">{title}</span>{close_tag}'
        )

    return H2_RE.sub(repl, body)


def wrap_tables(body: str) -> str:
    """Let wide tables scroll inside their own box instead of the page."""
    return TABLE_RE.sub(lambda m: f'<div class="table-wrap">{m.group(0)}</div>', body)


def build_toc(tokens: list[dict], lang: str) -> str:
    """Render the sidebar list from the top-level headings.

    Part numbers ('parte 1', 'part 12') become a tabular column of their own so
    the labels line up; sections without a number span the full width.
    """
    items: list[str] = []
    for token in tokens:
        name = strip_tags(token["name"])
        anchor = token["id"]
        part = PART_RE.match(name)
        if part:
            number = re.sub(
                r"^\s*(?:parte|part)\s+", "", part.group(1), flags=re.IGNORECASE
            )
            label = part.group(2).strip()
            items.append(
                f'          <li><a href="#{anchor}">'
                f'<span class="n">{html.escape(number.zfill(2))}</span>'
                f'<span class="t">{html.escape(label)}</span></a></li>'
            )
        else:
            items.append(
                f'          <li class="no-num"><a href="#{anchor}">'
                f'<span class="t">{html.escape(name)}</span></a></li>'
            )
    if not items:
        return ""
    strings = STRINGS[lang]
    return (
        f'      <nav class="toc" aria-label="{html.escape(strings["toc_aria"])}">\n'
        f"        <details open>\n"
        f'          <summary>{html.escape(strings["toc"])}</summary>\n'
        "        <ol>\n" + "\n".join(items) + "\n        </ol>\n"
        "        </details>\n"
        "      </nav>"
    )


def make_description(deck: str | None, body: str) -> str:
    """Condense the deck (or the opening paragraph) into a meta description."""
    if deck:
        text = strip_tags(markdown.markdown(deck))
    else:
        match = re.search(r"<(p|blockquote)[^>]*>(.*?)</\1>", body, re.DOTALL)
        text = strip_tags(match.group(2)) if match else ""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= DESCRIPTION_LIMIT:
        return text
    clipped = text[:DESCRIPTION_LIMIT]
    cut = clipped.rsplit(" ", 1)[0].rstrip(" ,;:.—–-")
    return f"{cut}…"


# --------------------------------------------------------------------------- #
# template
# --------------------------------------------------------------------------- #

PAGE = """<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_tag}</title>
  <meta name="description" content="{description}">
  <meta name="author" content="Leonardo Dias · Arvor">
  <link rel="canonical" href="{canonical}">
{alternates}  <link rel="icon" href="img/arvor_logo.png">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Arvor Intelligence">
  <meta property="og:locale" content="{og_locale}">
  <meta property="og:title" content="{social_title}">
  <meta property="og:description" content="{description}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{og_image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Arvor Intelligence">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{social_title}">
  <meta name="twitter:description" content="{description}">
  <meta name="twitter:image" content="{og_image}">
  <link rel="stylesheet" href="assets/artigo.css">
</head>
<body>
  <a class="skip" href="#conteudo">{skip}</a>
  <div class="progress" role="presentation"></div>

  <header class="masthead">
    <div class="mast-inner">
      <a class="brand" href="index.html">
        <img src="img/arvor_logo.png" alt=""><span>Arvor Intelligence</span>
      </a>
      <nav class="mast-nav" aria-label="{nav_aria}">
{mast_links}      </nav>
    </div>
  </header>

  <main id="conteudo">
    <article class="shell">
      <header class="article-head">
        <p class="eyebrow">{eyebrow}</p>
        <h1>{headline}</h1>
{deck_html}        <p class="byline">
          <span><b>{minutes}</b> {reading}</span>
          <span><b>{words}</b> {words_label}</span>
        </p>
      </header>

{toc}

      <div class="prose">
{body}
      </div>
    </article>
  </main>

  <footer class="site-foot">
    <div class="foot-inner">
      <a class="foot-brand" href="index.html"><img src="img/arvor_logo.png" alt="">Arvor Intelligence</a>
      <p>{foot}</p>
      <p class="foot-links">
        <a href="index.html">{foot_home}</a>
        <a href="{source_name}">{foot_source}</a>
        <a href="https://github.com/ArvorCo/PNAD">{foot_repo}</a>
      </p>
    </div>
  </footer>

  <script>
    (function () {{
      var bar = document.querySelector(".progress");
      var article = document.querySelector(".prose");
      var toc = document.querySelector(".toc details");
      var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));

      /* Reading progress, measured over the prose only. */
      if (bar && article) {{
        var ticking = false;
        var draw = function () {{
          var top = article.offsetTop;
          var span = article.offsetHeight - window.innerHeight + 120;
          var done = span > 0 ? (window.scrollY - top + 120) / span : 0;
          bar.style.width = Math.min(Math.max(done, 0), 1) * 100 + "%";
          ticking = false;
        }};
        var request = function () {{
          if (!ticking) {{ ticking = true; requestAnimationFrame(draw); }}
        }};
        addEventListener("scroll", request, {{ passive: true }});
        addEventListener("resize", request);
        draw();
      }}

      /* The TOC is a <details>: open inline on desktop, collapsed on mobile. */
      if (toc) {{
        var wide = matchMedia("(min-width: 1024px)");
        var sync = function () {{ toc.open = wide.matches; }};
        sync();
        wide.addEventListener("change", sync);
        links.forEach(function (link) {{
          link.addEventListener("click", function () {{
            if (!wide.matches) {{ toc.open = false; }}
          }});
        }});
      }}

      /* Highlight the section being read. */
      if (links.length && "IntersectionObserver" in window) {{
        var byId = {{}};
        links.forEach(function (link) {{ byId[link.getAttribute("href").slice(1)] = link; }});
        var targets = Object.keys(byId)
          .map(function (id) {{ return document.getElementById(id); }})
          .filter(Boolean);
        var seen = {{}};
        var mark = function () {{
          var current = null;
          targets.forEach(function (target) {{
            if (seen[target.id]) {{ current = target.id; }}
          }});
          if (!current) {{
            for (var i = targets.length - 1; i >= 0; i--) {{
              if (targets[i].getBoundingClientRect().top < 140) {{ current = targets[i].id; break; }}
            }}
          }}
          links.forEach(function (link) {{
            link.classList.toggle("is-active", link.getAttribute("href") === "#" + current);
          }});
        }};
        var observer = new IntersectionObserver(function (entries) {{
          entries.forEach(function (entry) {{ seen[entry.target.id] = entry.isIntersecting; }});
          mark();
        }}, {{ rootMargin: "-120px 0px -70% 0px" }});
        targets.forEach(function (target) {{ observer.observe(target); }});
        mark();
      }}
    }})();
  </script>
</body>
</html>
"""


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def indent(fragment: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(
        pad + line if line.strip() else line for line in fragment.splitlines()
    )


def render(article: Article, by_slug: dict[str, Article]) -> str:
    """Turn one Markdown source into the finished page."""
    raw = article.source.read_text(encoding="utf-8")
    title, deck, body_md = split_source(raw)
    strings = STRINGS[article.lang]

    converter = markdown.Markdown(
        extensions=["extra", "smarty", "sane_lists", "toc"],
        extension_configs={
            "toc": {
                "slugify": lambda value, sep: slugify(value, sep),
                "toc_depth": "2-3",
            },
            "smarty": {
                "smart_dashes": True,
                "smart_quotes": True,
                "smart_ellipses": True,
            },
        },
        output_format="html",
    )
    body = converter.convert(body_md)
    toc_tokens = converter.toc_tokens

    body = wrap_tables(body)
    body = label_note(body, strings["note"])
    body = mark_lede(body)
    body = mark_stats(body, article.lang)
    body = format_parts(body)

    words = count_words(body)
    minutes = max(1, round(words / WORDS_PER_MINUTE))
    headline = converter.reset().convert(title)
    headline = re.sub(r"^<p>|</p>$", "", headline).strip()
    deck_html = ""
    if deck:
        rendered = re.sub(r"^<p>|</p>$", "", converter.reset().convert(deck)).strip()
        deck_html = f'        <p class="deck">{rendered}</p>\n'

    # masthead: companion dossier / interactive essay, then the language toggle
    mast: list[str] = [
        f'        <a class="mast-link home" href="index.html">{html.escape(strings["home"])}</a>\n'
    ]
    if article.related:
        mast.append(
            f'        <a class="mast-link" href="{article.related.href}">'
            f"{html.escape(article.related.label)} →</a>\n"
        )
    if article.translation:
        other = by_slug[article.translation]
        mast.append(
            f'        <span class="lang" role="group" aria-label="{html.escape(strings["lang_label"])}">\n'
            f'          <span class="is-current" aria-current="true">{LANG_BADGE[article.lang]}</span>\n'
            f'          <a href="{other.filename}" hreflang="{other.lang}" lang="{other.lang}">'
            f"{LANG_BADGE[other.lang]}</a>\n"
            f"        </span>\n"
        )

    # hreflang: only meaningful when a translation exists
    alternates = ""
    if article.translation:
        other = by_slug[article.translation]
        alternates = (
            f'  <link rel="alternate" hreflang="{article.lang.lower()}" href="{SITE}/{article.filename}">\n'
            f'  <link rel="alternate" hreflang="{other.lang.lower()}" href="{SITE}/{other.filename}">\n'
            f'  <link rel="alternate" hreflang="x-default" href="{SITE}/{article.filename}">\n'
        )

    plain_title = strip_tags(headline)
    return PAGE.format(
        lang=article.lang,
        og_locale=article.lang.replace("-", "_") if "-" in article.lang else "en_US",
        title_tag=html.escape(f"{plain_title} · Arvor"),
        description=html.escape(make_description(deck, body), quote=True),
        social_title=html.escape(article.social_title or plain_title, quote=True),
        canonical=f"{SITE}/{article.filename}",
        og_image=OG_IMAGE,
        alternates=alternates,
        skip=html.escape(strings["skip"]),
        nav_aria=html.escape(strings["nav_aria"]),
        mast_links="".join(mast),
        eyebrow=html.escape(article.eyebrow),
        headline=headline,
        deck_html=deck_html,
        minutes=minutes,
        reading=html.escape(strings["reading"]),
        words=f"{words:,}".replace(",", "." if article.lang == "pt-BR" else ","),
        words_label=html.escape(strings["words"]),
        toc=build_toc(toc_tokens, article.lang),
        body=indent(body, 8),
        foot=html.escape(strings["foot"]),
        foot_home=html.escape(strings["foot_home"]),
        foot_source=html.escape(strings["foot_source"]),
        foot_repo=html.escape(strings["foot_repo"]),
        source_name=article.source.name,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render docs/artigo_*.md into long-read HTML pages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: uv run --with markdown python3 docs/build_articles.py",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DOCS,
        metavar="DIR",
        help="directory for the generated HTML (default: docs/)",
    )
    parser.add_argument(
        "--only",
        action="append",
        metavar="SLUG",
        help="build a single article; repeatable (default: all)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report what would change without writing (exit 1 if stale)",
    )
    args = parser.parse_args(argv)

    by_slug = {article.slug: article for article in ARTICLES}
    selected = ARTICLES
    if args.only:
        unknown = sorted(set(args.only) - by_slug.keys())
        if unknown:
            parser.error(f"unknown slug(s): {', '.join(unknown)}")
        selected = tuple(by_slug[slug] for slug in args.only)

    args.output.mkdir(parents=True, exist_ok=True)
    stale = 0
    for article in selected:
        if not article.source.is_file():
            print(f"error: missing source {article.source}", file=sys.stderr)
            return 1
        page = render(article, by_slug)
        target = args.output / article.filename
        current = target.read_text(encoding="utf-8") if target.is_file() else None
        if current == page:
            print(
                f"  unchanged  {target.relative_to(Path.cwd()) if target.is_relative_to(Path.cwd()) else target}"
            )
            continue
        stale += 1
        if args.check:
            print(f"  STALE      {target.name}")
            continue
        target.write_text(page, encoding="utf-8")
        words = count_words(page)
        print(f"  wrote      {target.name}  ({words:,} words on page)")

    if args.check and stale:
        print(
            f"\n{stale} file(s) out of date; run without --check to regenerate.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
