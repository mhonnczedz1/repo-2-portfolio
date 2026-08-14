#!/usr/bin/env python3
"""Render a content.json into a self-contained, shareable project overview.

Usage:  python3 tools/render.py <slug> [--out PATH] [--no-backgrounds]

The output is one HTML file with the stylesheet inlined and every image base64
encoded, so it renders correctly wherever it is sent and fetches nothing.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".gif": "image/gif", ".webp": "image/webp", ".svg": "image/svg+xml"}
SIZE_WARN = 3 * 1024 * 1024

TOOLBAR = (
    '<div class="toolbar">\n'
    '  <button type="button" class="printbtn" onclick="window.print()">Save as PDF</button>\n'
    '  <span class="hint">A4, two pages. Reads correctly with background graphics on or off.'
    '</span>\n'
    '</div>'
)


def e(text) -> str:
    """Escape a content string for HTML."""
    return html.escape(str(text), quote=True)


def prose(text) -> str:
    """Escape a paragraph, then honour `backticks` as inline code.

    content.json stays free of markup: backticks are notation, the same way they are
    in markdown, and nothing else in the string is interpreted.
    """
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(text))


def identity_parts(f: dict) -> list:
    """Name, email, link. The link is anchored only when it really is a URL."""
    link = f.get("link", "")
    linked = (f'<a href="{e(link)}">{e(link)}</a>'
              if link.startswith(("http://", "https://")) else f"<span>{e(link)}</span>")
    return [f'<span>{e(f["name"])}</span>', f'<span>{e(f["email"])}</span>', linked]


def render_byline(f: dict) -> str:
    """The header copy of the identity, for a reader who never reaches the footer."""
    return '<p class="byline">\n  ' + "\n  ".join(identity_parts(f)) + "\n</p>"


def render_footer(f: dict) -> str:
    return "<footer>\n  " + "\n  ".join(identity_parts(f)) + "\n</footer>"


def render_header(c: dict) -> str:
    chips = "\n".join(
        f'  <li class="chip"><b>{e(ch["label"])}</b> {e(ch["value"])}</li>'
        for ch in c["chips"])
    return (f'<h1>{e(c["title"])}</h1>\n'
            f'<p class="sub">{e(c["tagline"])}</p>\n'
            f'{render_byline(c["footer"])}\n'
            f'<ul class="chips">\n{chips}\n</ul>\n'
            f'<p class="result"><span class="label">What is it?</span>{e(c["result"])}</p>')


def render_prose(heading: str, paragraphs, pre: str = "", post: str = "") -> str:
    """A section, or nothing at all when it has no content."""
    paragraphs = list(paragraphs or [])
    if not (paragraphs or pre or post):
        return ""
    chunks = ["<section>", f"  <h2>{e(heading)}</h2>"]
    if pre:
        chunks.append(pre)
    chunks += [f"  <p>{prose(p)}</p>" for p in paragraphs]
    if post:
        chunks.append(post)
    chunks.append("</section>")
    return "\n".join(chunks)


def render_bullets(heading: str, items) -> str:
    """A bulleted section. Out-of-Scope reads as a list of choices, not a paragraph."""
    items = list(items or [])
    if not items:
        return ""
    lis = "\n".join(f"    <li>{prose(x)}</li>" for x in items)
    return (f"<section>\n  <h2>{e(heading)}</h2>\n"
            f'  <ul class="bullets">\n{lis}\n  </ul>\n</section>')


def data_uri(path: Path) -> str | None:
    """A base64 data URI for an image, or None when the file is not there."""
    if not path.is_file():
        return None
    mime = MIME.get(path.suffix.lower())
    if mime is None:
        raise SystemExit(f"unsupported image type: {path.name}")
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def figure(inner: str, caption: str) -> str:
    cap = f'\n    <figcaption><b>Fig 1.</b> {e(caption)}</figcaption>' if caption else ""
    return f"  <figure>\n{inner}{cap}\n  </figure>"


# What each legend entry explains. Only the types a diagram actually uses are worth listing.
LEGEND = {"own": ("", "own component"), "ext": ("l-ext", "third party"),
          "ai": ("l-ai", "model step"), "store": ("l-store", "datastore")}


def render_legend(legend) -> str:
    """A legend from a list of node types. True means all of them, absent means none."""
    if not legend:
        return ""
    kinds = list(LEGEND) if legend is True else list(legend)
    rows = []
    for kind in kinds:
        cls, label = LEGEND[kind]
        rows.append(f'        <span class="{cls}">{label}</span>' if cls
                    else f"        <span>{label}</span>")
    return '\n      <div class="legend">\n' + "\n".join(rows) + "\n      </div>"


def render_diagram(d: dict, base: Path) -> str:
    if d.get("mode") == "image":
        uri = data_uri(base / d["image"])
        inner = (f'    <img src="{uri}" alt="Architecture diagram">' if uri
                 else f'    <div class="slot">{e(d["image"])}</div>')
        return figure(inner, d.get("caption", ""))

    rows = []
    for i, tier in enumerate(d["tiers"]):
        if i:
            rows.append('      <span class="arrow down">&darr;</span>')
        nodes = []
        for j, n in enumerate(tier["nodes"]):
            if j:
                nodes.append('        <span class="arrow">&rarr;</span>')
            cls = "node" + (f' {n["type"]}' if n.get("type") else "")
            note = f'<span class="note">{e(n["note"])}</span>' if n.get("note") else ""
            nodes.append(f'        <div class="{cls}">{e(n["text"])}{note}</div>')
        rows.append(f'      <div class="tier" data-label="{e(tier["label"])}">\n'
                    + "\n".join(nodes) + "\n      </div>")

    legend = render_legend(d.get("legend"))
    return figure('    <div class="arch">\n' + "\n".join(rows) + legend + "\n    </div>",
                  d.get("caption", ""))


def render_gallery(items, base: Path) -> str:
    """2 to 5 equal images, one sentence each. Column count is derived from the count.

    Each image expands with no JavaScript: the thumbnail links to its own figure, and
    `.shot:target img` in the stylesheet lifts that same img into a fixed overlay. Nothing
    is duplicated, so a five image gallery costs no more payload than the thumbnails do.
    """
    items = list(items or [])
    if not items:
        return ""
    cols = 3 if len(items) in (3, 5) else 2
    figs = []
    for i, s in enumerate(items, 1):
        uri = data_uri(base / s["src"])
        if uri:
            media = (f'      <a class="zoom" href="#shot-{i}">'
                     f'<img src="{uri}" alt="Screenshot {i}"></a>\n'
                     f'      <a class="close" href="#gallery">Close</a>')
        else:
            media = f'      <div class="slot">{e(s["src"])}</div>'
        figs.append(f'    <figure class="shot" id="shot-{i}">\n{media}\n'
                    f'      <figcaption>{e(s["caption"])}</figcaption>\n    </figure>')
    return (f'<section id="gallery">\n  <h2>Gallery</h2>\n  <div class="gallery cols{cols}">\n'
            + "\n".join(figs) + "\n  </div>\n</section>")


def render_metrics(metrics) -> str:
    metrics = list(metrics or [])
    if not metrics:
        return ""
    cls = "metrics two" if len(metrics) == 2 else "metrics"
    tiles = "\n".join(
        f'    <div class="metric"><div class="val">{e(m["value"])}</div>'
        f'<div class="lbl">{e(m["label"])}</div></div>' for m in metrics)
    return f'  <div class="{cls}">\n{tiles}\n  </div>'


def render_decisions(items) -> str:
    lis = "\n".join(
        f'    <li><b>{e(x["chose"])} over {e(x["over"])}:</b> {e(x["because"])}</li>'
        for x in items)
    return ("<section>\n  <h2>Decisions and tradeoffs</h2>\n"
            f'  <ul class="decisions">\n{lis}\n  </ul>\n</section>')


def render(content: dict, base: Path, no_backgrounds: bool = False) -> str:
    """The whole document, as one self-contained string."""
    style = (ASSETS / "style.css").read_text(encoding="utf-8")
    if no_backgrounds:
        style += ("\n  /* variant: prove nothing depends on a background fill */\n"
                  "  *{ background:transparent !important; }\n")
    body = "\n\n".join(part for part in [
        render_header(content),
        render_prose("Problem", content["problem"]),
        render_prose("Architecture", content["architecture"],
                     post=render_diagram(content["diagram"], base)),
        render_decisions(content["decisions"]),
        render_prose("Impact", content["impact"],
                     pre=render_metrics(content.get("metrics", []))),
        render_gallery(content.get("gallery", []), base),
        render_bullets("Out-of-Scope", content["out_of_scope"]),
        render_footer(content["footer"]),
    ] if part)
    shell = (ASSETS / "shell.html").read_text(encoding="utf-8")
    return (shell.replace("{{title}}", e(content["title"]))
                 .replace("{{style}}", style)
                 .replace("{{toolbar}}", TOOLBAR)
                 .replace("{{body}}", body))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render a shareable project overview.")
    ap.add_argument("slug", help="directory name under overviews/")
    ap.add_argument("--out", help="output path (default out/overview-<slug>.html)")
    ap.add_argument("--no-backgrounds", action="store_true",
                    help="neutralise every background fill, to prove print safety")
    a = ap.parse_args(argv)

    base = ROOT / "overviews" / a.slug
    src = base / "content.json"
    if not src.is_file():
        print(f"no content at {src}", file=sys.stderr)
        return 1

    content = json.loads(src.read_text(encoding="utf-8"))
    out = Path(a.out) if a.out else ROOT / "out" / f"overview-{a.slug}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(content, base, a.no_backgrounds), encoding="utf-8")

    size = out.stat().st_size
    print(f"wrote {out}  ({size / 1024:.0f}KB)")
    if size > SIZE_WARN:
        print("  warning: over 3MB is awkward to send. Downscale the screenshots:")
        print(f"    sips -Z 1200 {base / 'images'}/*.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
