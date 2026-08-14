"""The rendered overview must match the committed version 3 snapshot exactly.

This is not version 1 parity. That was proved once, at 148 identical tokens, and version 3
changes the design on purpose. What this guards now is accidental change: edit the renderer
or the stylesheet in a way that moves the markup, and this fails.

When the change is deliberate, regenerate the snapshot and review the diff:

    python3 tools/render.py multi-tenant-rag-api \
        --out tests/golden/overview-multi-tenant-rag-api.html

The version 1 document is kept at tests/golden/v1/ as history. Nothing asserts against it.
"""
import json
import unittest
from pathlib import Path

from tests.helpers import normalise, structure
from tools.render import render

ROOT = Path(__file__).resolve().parent.parent
SLUG = "multi-tenant-rag-api"


class GoldenTest(unittest.TestCase):
    maxDiff = None

    def test_rendered_output_matches_the_version_three_snapshot(self):
        base = ROOT / "overviews" / SLUG
        content = json.loads((base / "content.json").read_text(encoding="utf-8"))
        got = render(content, base)
        want = (ROOT / "tests" / "golden" / f"overview-{SLUG}.html").read_text(encoding="utf-8")
        self.assertEqual(structure(normalise(want)), structure(normalise(got)),
                         "the design moved. If that was deliberate, regenerate the snapshot")
