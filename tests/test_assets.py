"""The stylesheet must be the version 1 one, verbatim, plus additions only."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden" / "overview-multi-tenant-rag-api.html"


def golden_style() -> str:
    doc = GOLDEN.read_text(encoding="utf-8")
    return re.search(r"<style>(.*?)</style>", doc, re.S).group(1)


class AssetsTest(unittest.TestCase):
    def test_stylesheet_starts_with_version_one_verbatim(self):
        css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
        self.assertTrue(css.startswith(golden_style()),
                        "version 1 CSS must be extracted byte for byte, additions appended after")

    def test_stylesheet_adds_toolbar_and_two_up_metrics(self):
        css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
        for needed in (".toolbar", ".printbtn", ".metrics.two"):
            self.assertIn(needed, css)

    def test_shell_has_every_placeholder_and_fetches_nothing(self):
        shell = (ROOT / "assets" / "shell.html").read_text(encoding="utf-8")
        for token in ("{{title}}", "{{style}}", "{{toolbar}}", "{{body}}"):
            self.assertIn(token, shell)
        self.assertNotIn("<link", shell)
        self.assertNotIn("@import", shell)
