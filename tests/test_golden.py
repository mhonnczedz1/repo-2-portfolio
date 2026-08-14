"""Rendering the version 1 overview from content.json must reproduce it exactly."""
import json
import unittest
from pathlib import Path

from tests.helpers import normalise, structure
from tools.render import render

ROOT = Path(__file__).resolve().parent.parent
SLUG = "multi-tenant-rag-api"


class GoldenTest(unittest.TestCase):
    maxDiff = None

    def test_rendered_output_matches_version_one(self):
        base = ROOT / "overviews" / SLUG
        content = json.loads((base / "content.json").read_text(encoding="utf-8"))
        got = render(content, base)
        want = (ROOT / "tests" / "golden" / f"overview-{SLUG}.html").read_text(encoding="utf-8")
        self.assertEqual(structure(normalise(want)), structure(normalise(got)))
