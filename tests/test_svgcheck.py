"""A hand-authored diagram cannot be looked at here, so its geometry is checked instead.

Each test breaks exactly one thing in a fixture that otherwise passes, which is the same
shape as tests/test_check.py.
"""
import tempfile
import unittest
from pathlib import Path

from tools.svgcheck import check_svg, svg_words, text_width

ROOT = Path(__file__).resolve().parent.parent
FLOW = ROOT / "tests" / "fixtures" / "flow.svg"


def variant(**replacements) -> Path:
    """The fixture with substrings swapped, written to a temp file."""
    doc = FLOW.read_text(encoding="utf-8")
    for old, new in replacements.items():
        doc = doc.replace(old.replace("__", " "), new)
    tmp = Path(tempfile.mkdtemp()) / "architecture.svg"
    tmp.write_text(doc, encoding="utf-8")
    return tmp


class WidthTest(unittest.TestCase):
    METRICS = (13, 1.0, 0)

    def test_capitals_are_wider_than_narrow_lowercase(self):
        self.assertGreater(text_width("MMM", self.METRICS), text_width("iii", self.METRICS))

    def test_character_count_alone_would_be_wrong(self):
        """Same length, very different printed width. This is why counting chars is not enough."""
        self.assertGreater(text_width("WWWW", self.METRICS) / text_width("llll", self.METRICS), 2)

    def test_letter_spacing_widens_a_label(self):
        self.assertGreater(text_width("PATH", (10, 1.0, 0.9)), text_width("PATH", (10, 1.0, 0)))


class ValidFlowTest(unittest.TestCase):
    def test_the_fixture_passes(self):
        self.assertEqual(check_svg(FLOW), [])

    def test_words_are_extracted_for_the_budget(self):
        self.assertEqual(svg_words(FLOW), ["PATH", "client", "upload", "API", "FastAPI", "write"])

    def test_a_missing_file_is_reported_not_raised(self):
        self.assertTrue(any("not found" in x for x in check_svg(FLOW.parent / "nope.svg")))

    def test_words_of_a_missing_file_are_empty(self):
        self.assertEqual(svg_words(FLOW.parent / "nope.svg"), [])


class GeometryFailureTest(unittest.TestCase):
    def test_a_note_wider_than_its_box_fails(self):
        path = variant(upload="upload a document, then wait for the embedding")
        self.assertTrue(any("overflows" in x for x in check_svg(path)), check_svg(path))

    def test_a_title_wider_than_its_box_fails(self):
        path = variant(client="client application endpoint name")
        self.assertTrue(any("overflows" in x for x in check_svg(path)))

    def test_a_floating_label_landing_on_a_box_fails(self):
        # long enough to reach the second box, and lifted to that box's vertical band
        path = variant(**{'x="130"__y="95">write': 'x="130" y="55">write into the index'})
        self.assertTrue(any("sits on top of" in x for x in check_svg(path)), check_svg(path))

    def test_two_labels_on_top_of_each_other_fails(self):
        path = variant(**{'x="36"__y="61">upload': 'x="36" y="48">upload'})
        self.assertTrue(any("labels overlap" in x for x in check_svg(path)), check_svg(path))

    def test_overlapping_boxes_fail(self):
        path = variant(**{'x="160"__y="30"__width="110"': 'x="100" y="30" width="110"'})
        self.assertTrue(any("boxes overlap" in x for x in check_svg(path)))

    def test_a_box_off_canvas_fails(self):
        path = variant(**{'x="160"__y="30"__width="110"': 'x="260" y="30" width="110"'})
        self.assertTrue(any("leaves the canvas" in x for x in check_svg(path)))

    def test_a_class_with_no_font_size_cannot_be_measured(self):
        path = variant(**{'class="t"__x="36"': 'class="mystery" x="36"'})
        self.assertTrue(any("no font-size" in x for x in check_svg(path)))

    def test_malformed_xml_fails_instead_of_raising(self):
        tmp = Path(tempfile.mkdtemp()) / "broken.svg"
        tmp.write_text("<svg><rect></svg>", encoding="utf-8")
        self.assertTrue(any("well-formed" in x for x in check_svg(tmp)))

    def test_a_missing_viewbox_fails(self):
        path = variant(**{'viewBox="0__0__300__120"': 'data-no-viewbox="1"'})
        self.assertTrue(any("viewBox" in x for x in check_svg(path)))


if __name__ == "__main__":
    unittest.main()
