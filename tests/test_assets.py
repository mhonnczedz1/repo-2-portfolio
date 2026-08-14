"""The stylesheet is the version 3 design: screen first, print compacts it back to A4.

Version 1 parity is deliberately no longer asserted. It was proved once, by the golden
comparison at 148 identical tokens, and holding it would mean expressing every intentional
design change as an override appended after the rule it contradicts. `tests/test_golden.py`
guards against accidental change instead.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE = ROOT / "assets" / "style.css"


def sheet() -> str:
    return STYLE.read_text(encoding="utf-8")


def print_rules(css: str) -> str:
    """The print block, which is the last thing in the file and compacts the screen design."""
    i = css.index("@media print{")
    return css[i:]


class StylesheetTest(unittest.TestCase):
    def test_screen_page_width_is_a_variable(self):
        """Three elements share the page width, so it cannot live in one of them."""
        css = sheet()
        self.assertRegex(css, r"--page:\s*\d+px")
        for selector in (".doc{", ".banner{", ".toolbar{"):
            block = css[css.index(selector):css.index("}", css.index(selector))]
            self.assertIn("var(--page)", block, f"{selector} must follow the shared page width")

    def test_print_block_actually_compacts(self):
        """Version 2 print was 8 lines of touch-up. Version 3 has to undo the screen spacing."""
        rules = print_rules(sheet())
        self.assertGreater(rules.count(";"), 40,
                           "print must restore A4 density, not just hide the toolbar")
        self.assertIn(".doc{ max-width:none", rules)

    def test_inline_code_reads_with_backgrounds_off(self):
        """Every tint is paired with a border, so the print dialog setting cannot hide it."""
        css = sheet()
        block = css[css.index("\n  code{"):css.index("}", css.index("\n  code{"))]
        self.assertIn("background:", block)
        self.assertIn("border:", block)

    def test_both_gallery_grids_exist(self):
        css = sheet()
        self.assertIn(".gallery.cols2{", css)
        self.assertIn(".gallery.cols3{", css)

    def test_images_expand_without_javascript(self):
        css = sheet()
        self.assertIn(".shot:target img{", css)
        self.assertIn(".shot .close{", css)
        self.assertNotIn("javascript:", css)

    def test_an_expanded_image_never_prints(self):
        rules = print_rules(sheet())
        self.assertIn(".shot:target img{", rules)
        self.assertIn(".shot .close{ display:none !important; }", rules)

    def test_result_label_and_bullet_list_are_styled(self):
        css = sheet()
        self.assertIn(".result .label{", css)
        self.assertIn("ul.bullets{", css)

    def test_subtitle_is_smaller_than_the_body_and_italic(self):
        css = sheet()
        block = css[css.index("  .sub{"):css.index("}", css.index("  .sub{"))]
        self.assertIn("font-style:italic", block)
        size = float(re.search(r"font-size:([\d.]+)pt", block).group(1))
        body = float(re.search(r"font:([\d.]+)pt/", css).group(1))
        self.assertLess(size, body)

    def test_stylesheet_is_navigable(self):
        """It is the single source of design, so the section headers earn their place."""
        self.assertGreaterEqual(sheet().count("/* ----------"), 7)


class ShellTest(unittest.TestCase):
    def test_shell_has_every_placeholder_and_fetches_nothing(self):
        shell = (ROOT / "assets" / "shell.html").read_text(encoding="utf-8")
        for token in ("{{title}}", "{{style}}", "{{toolbar}}", "{{body}}"):
            self.assertIn(token, shell)
        self.assertNotIn("<link", shell)
        self.assertNotIn("@import", shell)
