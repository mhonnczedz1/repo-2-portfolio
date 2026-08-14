"""Shared test helpers: the snapshot normaliser, and a mutable valid content fixture."""
import copy
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"

# Version 3 compares the renderer against its own committed snapshot, so the version 1
# bridging normalisations (placeholder spans, footer flattening) are gone. What remains
# makes the snapshot independent of whether images exist yet: a real screenshot becomes a
# zoom anchor wrapping an <img> plus a close link, and a missing one becomes a named slot.
# Both reduce to the same figure, so adding screenshots is not a design change.
NOISE = (
    re.compile(r'<a class="(?:zoom|close)"[^>]*>.*?</a>', re.S),
    re.compile(r"<img\b[^>]*>", re.S),
    re.compile(r'<div class="slot">.*?</div>', re.S),
)


def normalise(doc: str) -> str:
    for pat in NOISE:
        doc = pat.sub("", doc)
    return doc


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
