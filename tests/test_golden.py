"""The renderer must keep matching its committed design snapshot.

This is not version 1 parity. That was proved once, at 148 identical tokens, and version 3
changes the design on purpose. What this guards now is accidental change: edit the renderer
or the stylesheet in a way that moves the markup, and this fails.

It renders `tests/fixtures/valid.json`, not a real project, for two reasons. The fixture
exercises every optional section, and its image files deliberately do not exist, so the
snapshot stays a few kilobytes instead of carrying a megabyte of base64 that would churn
every time a screenshot is replaced.

When a design change is deliberate, regenerate the snapshot and read the diff:

    python3 -m tests.test_golden --write

The version 1 document is kept at tests/golden/v1/ as history. Nothing asserts against it.
"""
import json
import sys
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, normalise, structure
from tools.render import render

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "tests" / "golden" / "design-snapshot.html"


def rendered() -> str:
    content = json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8"))
    return render(content, FIXTURES)


class GoldenTest(unittest.TestCase):
    maxDiff = None

    def test_rendered_output_matches_the_design_snapshot(self):
        want = SNAPSHOT.read_text(encoding="utf-8")
        self.assertEqual(structure(normalise(want)), structure(normalise(rendered())),
                         "the design moved. If that was deliberate: "
                         "python3 -m tests.test_golden --write")

    def test_the_snapshot_carries_no_image_payload(self):
        """A snapshot that inlines screenshots churns by a megabyte on every recapture."""
        self.assertNotIn("base64,", SNAPSHOT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if "--write" in sys.argv:
        SNAPSHOT.write_text(rendered(), encoding="utf-8")
        print(f"wrote {SNAPSHOT.relative_to(ROOT)}  ({SNAPSHOT.stat().st_size / 1024:.0f}KB)")
    else:
        unittest.main()
