"""The stylesheet must be the version 1 one, verbatim, plus additions only."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden" / "overview-multi-tenant-rag-api.html"


def golden_style() -> str:
    doc = GOLDEN.read_text(encoding="utf-8")
    return re.search(r"<style>(.*?)</style>", doc, re.S).group(1)


def rules(css: str) -> str:
    """Declarations only. Comments and whitespace do not render, so they do not count."""
    return re.sub(r"\s+", " ", re.sub(r"/\*.*?\*/", "", css, flags=re.S)).strip()


class AssetsTest(unittest.TestCase):
    def test_stylesheet_keeps_every_version_one_rule_in_order(self):
        css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
        self.assertTrue(rules(css).startswith(rules(golden_style())),
                        "version 1 rules must survive unchanged and in order, additions appended")

    def test_stylesheet_is_navigable(self):
        """It is the single source of design now, so the section headers earn their place."""
        css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
        self.assertGreaterEqual(css.count("/* ----------"), 7)

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
