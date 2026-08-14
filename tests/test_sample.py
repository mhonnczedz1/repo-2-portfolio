"""The sample that ships with the repo must be self-contained and must not go stale.

It is the first thing someone browsing the repo opens, so a sample rendered by an older
version of the design would misrepresent the tool. Regenerate it with:

    python3 tools/make_sample.py
"""
import json
import re
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, normalise, structure
from tools.check import check_output
from tools.render import render

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "overview-example.html"


class SampleTest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.doc = SAMPLE.read_text(encoding="utf-8")

    def test_the_sample_exists_and_fetches_nothing(self):
        self.assertEqual(check_output(SAMPLE), [])
        for src in re.findall(r'src="([^"]*)"', self.doc):
            self.assertTrue(src.startswith("data:"), src)

    def test_the_sample_shows_a_populated_gallery(self):
        """Empty dashed boxes would not show that the gallery works."""
        self.assertGreaterEqual(len(re.findall(r'src="data:image/png;base64,', self.doc)), 2)
        self.assertIn('class="zoom"', self.doc)

    def test_the_sample_publishes_no_real_identity(self):
        self.assertIn("you@example.com", self.doc)

    def test_the_sample_matches_the_current_design(self):
        content = json.loads((FIXTURES / "valid.json").read_text(encoding="utf-8"))
        current = render(content, FIXTURES)
        self.assertEqual(structure(normalise(current)), structure(normalise(self.doc)),
                         "the sample is stale. Run: python3 tools/make_sample.py")
