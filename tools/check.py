#!/usr/bin/env python3
"""Validate a project overview before it ships.

Usage:  python3 tools/check.py <slug> [--strict]

Checks content.json against the word budget and the quality bar, and checks the
rendered output when it exists. Exits non-zero on any hard failure. --strict also
fails on unresolved TODO(verify) claims, which is the gate before sending.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BUDGETS = {"header": 60, "identity": 14, "problem": 75, "architecture": 190, "diagram": 55,
           "gallery": 50, "decisions": 140, "impact": 85, "out_of_scope": 30}
TOTAL = 700
TODO = "TODO(verify)"
CAPTION_WORDS = 14          # a gallery caption is one sentence, not a paragraph
GALLERY_MAX = 5
REQUIRED = {"slug": str, "title": str, "tagline": str, "chips": list, "result": str,
            "problem": list, "architecture": list, "diagram": dict, "decisions": list,
            "impact": list, "out_of_scope": list, "footer": dict}


def words(*texts) -> int:
    """Printed words. The TODO marker is scaffolding and does not count."""
    return len(" ".join(str(t) for t in texts if t).replace(TODO, " ").split())


def section_texts(c: dict) -> dict:
    """Every string that prints, grouped by the budget line it belongs to."""
    d = c.get("diagram") or {}
    diagram = [d.get("caption", "")]
    for tier in d.get("tiers", []):
        diagram.append(tier.get("label", ""))
        for n in tier.get("nodes", []):
            diagram += [n.get("text", ""), n.get("note") or ""]
    f = c.get("footer") or {}
    identity = [f.get("name", ""), f.get("email", ""), f.get("link", "")]
    return {
        "header": [c.get("title", ""), c.get("tagline", ""), c.get("result", "")]
                  + [f'{ch.get("label", "")} {ch.get("value", "")}' for ch in c.get("chips", [])],
        # printed twice, in the header byline and in the footer, so counted twice
        "identity": identity * 2,
        "problem": list(c.get("problem", [])),
        "architecture": list(c.get("architecture", [])),
        "diagram": diagram,
        "gallery": [s.get("caption", "") for s in c.get("gallery", [])],
        "decisions": [f'{x.get("chose", "")} over {x.get("over", "")} {x.get("because", "")}'
                      for x in c.get("decisions", [])],
        "impact": list(c.get("impact", []))
                  + [f'{m.get("value", "")} {m.get("label", "")}' for m in c.get("metrics", [])],
        "out_of_scope": list(c.get("out_of_scope", [])),
    }


def check_schema(c: dict) -> list:
    out = []
    for field, kind in REQUIRED.items():
        if field not in c:
            out.append(f"{field}: required field is missing")
        elif not isinstance(c[field], kind):
            out.append(f"{field}: expected {kind.__name__}, found {type(c[field]).__name__}")
        elif not c[field]:
            out.append(f"{field}: required field is empty")
    return out


def check_budgets(c: dict) -> list:
    out, total = [], 0
    for name, texts in section_texts(c).items():
        n = words(*texts)
        total += n
        if n > BUDGETS[name]:
            out.append(f"{name}: {n} words, budget {BUDGETS[name]}, over by {n - BUDGETS[name]}")
    if total > TOTAL:
        out.append(f"total: {total} words, hard limit {TOTAL}, over by {total - TOTAL}")
    return out


BANNED = re.compile(
    r"\b(robust\w*|seamless\w*|cutting-edge|leverag\w*|utilis\w*|utiliz\w*)\b", re.I)
NODE_TYPES = {"core", "ext", "store", "ai"}


def check_banned(c: dict) -> list:
    out = []
    for section, texts in section_texts(c).items():
        for hit in BANNED.findall(" ".join(str(t) for t in texts if t)):
            out.append(f"{section}: banned superlative {hit!r}, say what it actually does")
    return out


def check_decisions(c: dict) -> list:
    out = []
    for i, d in enumerate(c.get("decisions", []), 1):
        for field in ("chose", "over", "because"):
            if not str(d.get(field, "")).strip():
                out.append(f"decision {i}: {field!r} is missing. "
                           "A bullet with no rejected alternative is a fact, not a decision")
    return out


def check_diagram(c: dict, base: Path) -> list:
    d = c.get("diagram") or {}
    out = []
    if d.get("mode") == "image":
        if not (base / d.get("image", "")).is_file():
            out.append(f"diagram: image {d.get('image')!r} not found")
        return out

    tiers = d.get("tiers") or []
    if not 2 <= len(tiers) <= 4:
        out.append(f"diagram: {len(tiers)} tiers, expected 2 to 4")
    nodes = [n for tier in tiers for n in tier.get("nodes", [])]
    if len(nodes) > 12:
        out.append(f"diagram: {len(nodes)} nodes, more than 12 stops being readable at a glance")
    cores = sum(1 for n in nodes if n.get("type") == "core")
    if cores != 1:
        out.append(f"diagram: found {cores} core nodes, expected exactly 1")
    for n in nodes:
        kind = n.get("type")
        if kind and kind not in NODE_TYPES:
            out.append(f"diagram: unknown node type {kind!r}, "
                       f"expected one of {', '.join(sorted(NODE_TYPES))}")
    return out


def check_counts(c: dict) -> list:
    out = []
    if len(c.get("chips", [])) > 5:
        out.append(f"chips: {len(c['chips'])}, keep it to 5")
    if len(c.get("metrics", [])) == 1:
        out.append("metrics: one tile looks like a stray number. Use 2, 3, or none")
    gallery = c.get("gallery") or []
    if gallery and not 2 <= len(gallery) <= GALLERY_MAX:
        out.append(f"gallery: {len(gallery)} images. Use 2 to {GALLERY_MAX}, or omit the section")
    for i, s in enumerate(gallery, 1):
        n = words(s.get("caption", ""))
        if n > CAPTION_WORDS:
            out.append(f"gallery: caption {i} is {n} words, cap {CAPTION_WORDS}. "
                       "One sentence saying what the screen proves")
    return out


def warnings(c: dict) -> list:
    out = []
    outstanding = sum(str(t).count(TODO) for texts in section_texts(c).values() for t in texts)
    if outstanding:
        out.append(f"{outstanding} unresolved {TODO} claim(s). Resolve or delete before sending")
    if len(c.get("decisions", [])) > 4:
        out.append(f"decisions: {len(c['decisions'])} bullets, 3 to 4 reads better")
    for i, tier in enumerate((c.get("diagram") or {}).get("tiers", []), 1):
        n = len(tier.get("nodes", []))
        if not 3 <= n <= 5:
            out.append(f"tier {i} ({tier.get('label')}): {n} nodes, 3 to 5 reads best")
    return out


SIZE_WARN = 3 * 1024 * 1024
REMOTE = re.compile(r'\ssrc\s*=\s*["\'](?:https?:)?//', re.I)
IMPORT = re.compile(r"@import", re.I)
CSS_URL = re.compile(r"url\(\s*['\"]?(?:https?:)?//", re.I)


def check_output(path: Path) -> list:
    """The artifact must fetch nothing to render itself. Anchors are fine."""
    doc = path.read_text(encoding="utf-8")
    out = []
    if REMOTE.search(doc):
        out.append("output: a remote src would break the file once it is shared")
    if re.search(r"<link\b", doc, re.I):
        out.append("output: a <link> element means the stylesheet is not inlined")
    if IMPORT.search(doc):
        out.append("output: an @import fetches CSS at open time")
    if CSS_URL.search(doc):
        out.append("output: a remote url(...) in CSS fetches at open time")
    return out


def report(slug: str, strict: bool = False) -> int:
    base = ROOT / "overviews" / slug
    src = base / "content.json"
    if not src.is_file():
        print(f"no content at {src}")
        return 1
    c = json.loads(src.read_text(encoding="utf-8"))

    print(f"\n{src}")
    counts = {name: words(*texts) for name, texts in section_texts(c).items()}
    for name, budget in BUDGETS.items():
        flag = "  over" if counts[name] > budget else ""
        print(f"  {name:<13}{counts[name]:>4} / {budget}{flag}")
    print(f"  {'total':<13}{sum(counts.values()):>4} / {TOTAL}")

    errors = (check_schema(c) + check_budgets(c) + check_banned(c)
              + check_decisions(c) + check_diagram(c, base) + check_counts(c))

    out = ROOT / "out" / f"overview-{slug}.html"
    if out.is_file():
        errors += check_output(out)
        size = out.stat().st_size
        print(f"  output        {size / 1024:.0f}KB")
        if size > SIZE_WARN:
            print("  warning: over 3MB is awkward to send. Downscale the screenshots:")
            print(f"    sips -Z 1200 {base / 'images'}/*.png")

    notes = warnings(c)
    for w in notes:
        print(f"  warning: {w}")
    for x in errors:
        print(f"  FAIL {x}")

    if strict and any("TODO" in w for w in notes):
        print("  FAIL strict: unresolved TODO(verify) claims block sending")
        return 1
    return 1 if errors else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate a project overview.")
    ap.add_argument("slug", help="directory name under overviews/")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on unresolved TODO(verify), the gate before sending")
    a = ap.parse_args(argv)
    return report(a.slug, a.strict)


if __name__ == "__main__":
    sys.exit(main())
