#!/usr/bin/env python3
"""Render the sample overview that ships with the repo.

Usage:  python3 tools/make_sample.py

The sample is what someone browsing the repo opens to see what the tool produces. It
renders tests/fixtures/valid.json, which is the only example content the repo tracks,
because overviews/ is gitignored and belongs to whoever is using the tool.

Screenshots are painted here rather than committed. Real ones would be somebody's
actual product, and a sample with empty dashed boxes does not show that the gallery
works. Each mock is labelled as a sample so nobody mistakes it for a real capture.
"""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.render import render  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "valid.json"
SAMPLE = ROOT / "samples" / "overview-example.html"

# One tint per image, so the gallery reads as two different screens.
TINTS = ((124, 58, 237), (14, 116, 144), (180, 83, 9), (21, 128, 61), (190, 18, 60))


def png(width: int, height: int, rows: list) -> bytes:
    """A minimal 8 bit RGB PNG. Standard library only, like everything else here."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + row for row in rows)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def mock_screenshot(path: Path, tint: tuple) -> None:
    """A window bar, a sidebar, and text lines. Enough to judge the layout, nothing more."""
    W, H = 1200, 750
    white, grey, pale = bytes((255, 255, 255)), bytes((229, 231, 235)), bytes((246, 248, 250))
    bar = bytes(tint)
    rows = []
    for y in range(H):
        if y < 56:                                   # title bar
            rows.append(bar * W)
            continue
        row = bytearray()
        for x in range(W):
            if x < 220:                              # sidebar
                px = pale
            elif 90 < y < 640 and (y - 90) % 46 < 14 and 260 < x < 1040 - (y % 3) * 120:
                px = grey                            # a line of text
            else:
                px = white
            row += px
        rows.append(bytes(row))
    path.write_bytes(png(W, H, rows))


def main() -> int:
    content = json.loads(FIXTURE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "images").mkdir()
        for i, shot in enumerate(content.get("gallery", [])):
            mock_screenshot(base / shot["src"], TINTS[i % len(TINTS)])
        doc = render(content, base)

    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE.write_text(doc, encoding="utf-8")
    print(f"wrote {SAMPLE.relative_to(ROOT)}  ({SAMPLE.stat().st_size / 1024:.0f}KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
