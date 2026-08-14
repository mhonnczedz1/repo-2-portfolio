"""Shared test helpers: the golden normaliser, and a mutable valid content fixture."""
import copy
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

# The four declared normalisations. Everything else must match exactly.
NOISE = (
    re.compile(r"<img\b[^>]*>", re.S),                       # 1. build-time inlining
    re.compile(r'<div class="slot">.*?</div>', re.S),        # 2. missing-image is now static
)
PH_SPAN = re.compile(r'<span class="ph">(.*?)</span>', re.S)  # 3. no placeholder markup
FOOTER = re.compile(r"<footer>(.*?)</footer>", re.S)          # 4. link becomes an anchor

# Version 1 added .missing at runtime via onerror; version 2 decides it at build time.
# Same change as 2, so the class carries no signal for this comparison.
IGNORED_CLASSES = {"ph", "missing"}


def normalise(doc: str) -> str:
    for pat in NOISE:
        doc = pat.sub("", doc)
    doc = PH_SPAN.sub(r"\1", doc)

    def flatten(m):
        text = " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())
        return f"<footer>{text}</footer>"

    return FOOTER.sub(flatten, doc)


class _Doc(HTMLParser):
    """Flatten the div.doc subtree into a comparable token sequence."""

    VOID = {"img", "br", "hr", "meta", "input", "source"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens, self.depth = [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        if self.depth is None:
            if tag == "div" and "doc" in classes:
                self.depth = 0
            return
        classes -= IGNORED_CLASSES
        self.tokens.append((tag, " ".join(sorted(classes)), a.get("data-label", "")))
        if tag not in self.VOID:
            self.depth += 1

    def handle_endtag(self, tag):
        if self.depth is None or tag in self.VOID:
            return
        self.depth -= 1
        if self.depth < 0:
            self.depth = None

    def handle_data(self, data):
        if self.depth is None:
            return
        text = " ".join(data.split())
        if text:
            self.tokens.append(("#text", text, ""))


def structure(doc: str) -> list:
    p = _Doc()
    p.feed(doc)
    return p.tokens


def content(**overrides):
    """A valid content dict with overrides applied. One rule broken per test."""
    c = copy.deepcopy(json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8")))
    c.update(overrides)
    return c
