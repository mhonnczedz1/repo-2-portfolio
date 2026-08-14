#!/usr/bin/env python3
"""Verify a hand-authored flow diagram's geometry, and count the words it prints.

Usage:  python3 tools/svgcheck.py <path/to/architecture.svg>

No renderer runs in this environment (PLAN.md, Environment findings: Chromium cannot
launch and QuickLook is sandboxed), so geometry is checked arithmetically instead of
visually. That covers the failure a hand-authored diagram actually has: a label wider
than the box it sits in, a floating label landing on a node, or something off canvas.
Nothing here judges whether the diagram reads well. That stays a human call.

Widths come from Helvetica advance tables, because the system font stack resolves to
Helvetica metrics for width purposes on the platforms this document targets. Counting
characters instead would overestimate `.txt .md .pdf` and underestimate `POST /DOCS`,
which is the wrong error in both directions.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "{http://www.w3.org/2000/svg}"
MIN_SLACK = 4.0          # px to the right edge of its own box, below this it reads as touching
SWATCH_W = 24.0          # a rect narrower than this is decoration, not a node
ASCENDER = 0.78          # baseline to top of a capital, as a fraction of font size
SEMIBOLD = 1.06          # 600 weight runs about 6% wider than regular at the same size

# Helvetica advance widths, units per 1000 em.
W = {" ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
     "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
     "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
     "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
     "@": 1015, "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
     "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778,
     "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
     "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
     "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
     "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556,
     "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722,
     "x": 500, "y": 500, "z": 500, "{": 334, "|": 260, "}": 334, "~": 584}
FALLBACK = 556

STYLE_RULE = re.compile(r"\.([\w-]+)\s*\{([^}]*)\}")


def font_table(doc: str) -> dict:
    """Font metrics per class, read from the SVG's own style block.

    Derived rather than hardcoded, so retuning a size in the template cannot leave this
    checker silently measuring against the old one.
    """
    table = {}
    for cls, body in STYLE_RULE.findall(doc):
        size = re.search(r"font-size:\s*([\d.]+)px", body)
        if not size:
            continue
        weight = re.search(r"font-weight:\s*(\d+)", body)
        spacing = re.search(r"letter-spacing:\s*([\d.]+)em", body)
        px = float(size.group(1))
        table[cls] = (px,
                      SEMIBOLD if weight and int(weight.group(1)) >= 600 else 1.0,
                      float(spacing.group(1)) * px if spacing else 0.0)
    return table


def text_width(s: str, metrics: tuple) -> float:
    size, weight, spacing = metrics
    return sum(W.get(ch, FALLBACK) for ch in s) / 1000 * size * weight + spacing * len(s)


def num(el, key: str) -> float:
    return float(el.get(key, 0) or 0)


def parse(path: Path) -> tuple:
    """(viewBox, boxes, labels). A box is a node; the frame and swatches are not."""
    doc = path.read_text(encoding="utf-8")
    root = ET.fromstring(doc)                      # raises on malformed XML, which is a real failure
    fonts = font_table(doc)
    view = [float(v) for v in (root.get("viewBox") or "0 0 0 0").split()]

    rects, labels = [], []
    for el in root.iter():
        if el.tag == SVG + "rect":
            rects.append({"x": num(el, "x"), "y": num(el, "y"),
                          "w": num(el, "width"), "h": num(el, "height"),
                          "cls": (el.get("class") or "plain")})
        elif el.tag == SVG + "text":
            text = "".join(el.itertext()).strip()
            if not text:
                continue
            cls = (el.get("class") or "").split()[0] if el.get("class") else ""
            metrics = fonts.get(cls)
            w = text_width(text, metrics) if metrics else 0.0
            x = num(el, "x")
            anchor = el.get("text-anchor")
            if anchor == "middle":
                x -= w / 2
            elif anchor == "end":
                x -= w
            size = metrics[0] if metrics else 0.0
            labels.append({"text": text, "cls": cls, "known": metrics is not None,
                           "x": x, "y": num(el, "y") - size * ASCENDER, "w": w, "h": size})

    frame = max(rects, key=lambda r: r["w"] * r["h"], default=None)
    boxes = [r for r in rects if r is not frame and r["w"] >= SWATCH_W]
    return view, boxes, labels


def host(label: dict, boxes: list):
    """The smallest box containing a label's start, or None when it floats free."""
    mid = label["y"] + label["h"] / 2
    inside = [b for b in boxes
              if b["x"] <= label["x"] <= b["x"] + b["w"] and b["y"] <= mid <= b["y"] + b["h"]]
    return min(inside, key=lambda b: b["w"] * b["h"]) if inside else None


def overlaps(a: dict, b: dict) -> bool:
    return (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
            and a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"])


def check_svg(path: Path) -> list:
    """Geometry failures, one string each. Empty means the drawing holds together."""
    if not Path(path).is_file():
        return [f"svg {Path(path).name!r} not found"]
    try:
        view, boxes, labels = parse(Path(path))
    except ET.ParseError as error:
        return [f"svg is not well-formed XML: {error}"]

    out = []
    if len(view) != 4 or not view[2] or not view[3]:
        return [f"svg needs a viewBox with a width and height, found {view}"]

    for label in labels:
        if not label["known"]:
            out.append(f"label {label['text']!r} uses class {label['cls']!r}, which declares no "
                       "font-size, so its width cannot be checked")

    for label in labels:
        if not label["known"]:
            continue
        box = host(label, boxes)
        if box is None:                                  # a floating label: keep it off the boxes
            for other in boxes:
                if overlaps(label, other):
                    out.append(f"label {label['text']!r} sits on top of a {other['cls']!r} box")
            continue
        slack = (box["x"] + box["w"]) - (label["x"] + label["w"])
        if slack < MIN_SLACK:
            out.append(f"label {label['text']!r} overflows its {box['cls']!r} box by "
                       f"{MIN_SLACK - slack:.0f}px. Shorten it or widen the box")

    # Text on text is the one collision a reader cannot decode, and it survives every
    # other check: a label dropped inside a node box passes the fit test while printing
    # straight through that node's own title.
    sized = [x for x in labels if x["known"]]
    for i, a in enumerate(sized):
        for b in sized[i + 1:]:
            if overlaps(a, b):
                out.append(f"labels overlap: {a['text']!r} and {b['text']!r}")

    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if overlaps(a, b):
                out.append(f"boxes overlap: {a['cls']!r} and {b['cls']!r}")

    for item in boxes + labels:
        name = item.get("cls") if "text" not in item else repr(item["text"])
        if (item["x"] < view[0] or item["y"] < view[1]
                or item["x"] + item["w"] > view[0] + view[2]
                or item["y"] + item["h"] > view[1] + view[3]):
            out.append(f"{name} leaves the canvas ({view[2]:.0f}x{view[3]:.0f})")
    return out


def svg_words(path: Path) -> list:
    """Every string the diagram prints. These count against the diagram word budget."""
    path = Path(path)
    if not path.is_file():
        return []
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8"))
    except ET.ParseError:
        return []
    return [t for t in ("".join(el.itertext()).strip() for el in root.iter(SVG + "text")) if t]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check a flow diagram's geometry.")
    ap.add_argument("path", help="path to the SVG")
    a = ap.parse_args(argv)
    path = Path(a.path)

    errors = check_svg(path)
    if not path.is_file():
        print(errors[0])
        return 1

    view, boxes, labels = parse(path)
    print(f"\n{path}  {view[2]:.0f}x{view[3]:.0f}, {len(boxes)} boxes, {len(labels)} labels")
    for label in labels:
        box = host(label, boxes) if label["known"] else None
        if box:
            slack = (box["x"] + box["w"]) - (label["x"] + label["w"])
            note = "  tight" if slack < 8 else ""
            print(f"  {label['text'][:26]:<28}in {box['cls']:<6}slack {slack:>5.1f}px{note}")
        else:
            print(f"  {label['text'][:26]:<28}floating")
    words = sum(len(t.split()) for t in svg_words(path))
    print(f"  prints {words} words, which count against the 55 word diagram budget")
    for x in errors:
        print(f"  FAIL {x}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
