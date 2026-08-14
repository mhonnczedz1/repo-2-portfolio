"""The renderer turns content into markup, and never leaves a fetchable reference behind."""
import unittest
from pathlib import Path

from tools.render import (e, render, render_diagram, render_footer, render_header, render_metrics,
                          render_prose, render_shots)

ROOT = Path(__file__).resolve().parent.parent

CONTENT = {
    "slug": "demo", "title": "Demo Project",
    "tagline": "A service that does one thing for one team.",
    "chips": [{"label": "Role", "value": "solo build"}],
    "result": "Cut a two hour task to four minutes.",
    "problem": ["First paragraph.", "Second paragraph."],
    "architecture": ["Walk the request."],
    "diagram": {"mode": "kit", "caption": "One path in, one out.", "legend": False,
                "tiers": [{"label": "Ingest",
                           "nodes": [{"text": "API", "note": "FastAPI", "type": "core"}]}]},
    "decisions": [{"chose": "Namespaces", "over": "a collection per tenant",
                   "because": "isolation becomes a property of the query."}],
    "impact": ["Used by two teams."],
    "limits": ["Single node only. Next: a queue."],
    "footer": {"name": "A Name", "email": "a@b.com", "link": "https://example.com/repo"},
}


class RenderPartsTest(unittest.TestCase):
    def test_escapes_content(self):
        self.assertEqual(e('<b>&"'), "&lt;b&gt;&amp;&quot;")

    def test_header_has_chips_and_result(self):
        out = render_header(CONTENT)
        self.assertIn("<h1>Demo Project</h1>", out)
        self.assertIn('<li class="chip"><b>Role</b> solo build</li>', out)
        self.assertIn('<p class="result">Cut a two hour task to four minutes.</p>', out)

    def test_prose_puts_pre_before_and_post_after_paragraphs(self):
        out = render_prose("Impact", ["Body."], pre="<!--P-->", post="<!--Q-->")
        self.assertLess(out.index("<!--P-->"), out.index("<p>Body.</p>"))
        self.assertGreater(out.index("<!--Q-->"), out.index("<p>Body.</p>"))

    def test_prose_section_vanishes_when_empty(self):
        self.assertEqual(render_prose("Impact", []), "")

    def test_footer_links_a_real_url_and_plain_text_stays_a_span(self):
        self.assertIn('<a href="https://example.com/repo">', render_footer(CONTENT["footer"]))
        self.assertIn("<span>repo link</span>",
                      render_footer({"name": "N", "email": "e", "link": "repo link"}))


class RenderDocumentTest(unittest.TestCase):
    def setUp(self):
        self.doc = render(CONTENT, ROOT / "tests" / "fixtures")

    def test_title_is_the_project_name(self):
        self.assertIn("<title>Demo Project</title>", self.doc)

    def test_print_button_is_the_only_javascript(self):
        self.assertIn('onclick="window.print()"', self.doc)
        self.assertNotIn("<script", self.doc)
        self.assertNotIn("onerror", self.doc)

    def test_fetches_nothing(self):
        self.assertNotIn("<link", self.doc)
        self.assertNotIn("@import", self.doc)
        self.assertNotIn('src="http', self.doc)

    def test_stylesheet_is_inlined(self):
        self.assertIn("@page{ size:A4", self.doc)

    def test_no_backgrounds_variant_neutralises_fills(self):
        variant = render(CONTENT, ROOT / "tests" / "fixtures", no_backgrounds=True)
        self.assertIn("background:transparent !important", variant)


TWO_TIER = {
    "mode": "kit", "caption": "Retrieval is deterministic.", "legend": True,
    "tiers": [
        {"label": "Ingest", "nodes": [
            {"text": "Client", "note": "upload / HTTP", "type": "ext"},
            {"text": "API layer", "note": "FastAPI", "type": "core"}]},
        {"label": "Reason", "nodes": [
            {"text": "Embed", "note": "Ollama", "type": "ai"},
            {"text": "Index", "note": "ChromaDB", "type": "store"},
            {"text": "Merge", "note": None}]},
    ],
}


class DiagramTest(unittest.TestCase):
    def setUp(self):
        self.out = render_diagram(TWO_TIER, ROOT / "tests" / "fixtures")

    def test_node_types_become_classes(self):
        self.assertIn('<div class="node ext">Client<span class="note">upload / HTTP</span></div>',
                      self.out)
        self.assertIn('<div class="node core">API layer', self.out)

    def test_untyped_node_is_a_plain_node_with_no_note(self):
        self.assertIn('<div class="node">Merge</div>', self.out)

    def test_tier_label_rides_on_the_data_attribute(self):
        self.assertIn('<div class="tier" data-label="Ingest">', self.out)

    def test_arrows_go_between_nodes_and_between_tiers(self):
        self.assertEqual(self.out.count('<span class="arrow">&rarr;</span>'), 3)
        self.assertEqual(self.out.count('<span class="arrow down">&darr;</span>'), 1)

    def test_legend_is_opt_in(self):
        self.assertIn('<div class="legend">', self.out)
        self.assertNotIn('<div class="legend">',
                         render_diagram({**TWO_TIER, "legend": False},
                                        ROOT / "tests" / "fixtures"))

    def test_caption_is_numbered(self):
        self.assertIn("<b>Fig 1.</b> Retrieval is deterministic.", self.out)

    def test_image_mode_missing_file_degrades_to_a_named_slot(self):
        out = render_diagram({"mode": "image", "image": "architecture.png", "caption": "c"},
                             ROOT / "tests" / "fixtures")
        self.assertIn('<div class="slot">architecture.png</div>', out)
        self.assertNotIn("<img", out)


FIXTURES = ROOT / "tests" / "fixtures"


class ShotsTest(unittest.TestCase):
    def test_present_image_is_inlined_as_base64(self):
        out = render_shots([{"src": "pixel.png", "caption": "What it proves."}], FIXTURES)
        self.assertIn('<img src="data:image/png;base64,iVBORw0KGgo', out)
        self.assertNotIn('class="shot missing"', out)
        self.assertIn("<figcaption>What it proves.</figcaption>", out)

    def test_missing_image_becomes_a_named_placeholder(self):
        out = render_shots([{"src": "images/99-nope.png", "caption": "Caption survives."}],
                           FIXTURES)
        self.assertIn('<figure class="shot missing">', out)
        self.assertIn('<div class="slot">images/99-nope.png</div>', out)
        self.assertNotIn("<img", out)
        self.assertIn("Caption survives.", out)

    def test_section_vanishes_without_shots(self):
        self.assertEqual(render_shots([], FIXTURES), "")


class MetricsTest(unittest.TestCase):
    def test_three_tiles_use_the_default_grid(self):
        out = render_metrics([{"value": "95%", "label": "a"}, {"value": "2", "label": "b"},
                              {"value": "4 min", "label": "c"}])
        self.assertIn('<div class="metrics">', out)
        self.assertIn('<div class="val">95%</div>', out)

    def test_two_tiles_switch_to_the_two_up_grid(self):
        out = render_metrics([{"value": "95%", "label": "a"}, {"value": "2", "label": "b"}])
        self.assertIn('<div class="metrics two">', out)

    def test_grid_vanishes_without_numbers(self):
        self.assertEqual(render_metrics([]), "")


class InlineCodeTest(unittest.TestCase):
    def test_backticks_become_code_elements(self):
        out = render_prose("Architecture", ["`/ingest` takes a document."])
        self.assertIn("<p><code>/ingest</code> takes a document.</p>", out)

    def test_markup_in_content_is_still_escaped(self):
        out = render_prose("Problem", ["<script>alert(1)</script>"])
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)

    def test_an_unpaired_backtick_is_left_alone(self):
        self.assertIn("<p>a ` b</p>", render_prose("Problem", ["a ` b"]))


class LegendTest(unittest.TestCase):
    def test_legend_lists_only_the_types_asked_for(self):
        out = render_diagram({**TWO_TIER, "legend": ["ext", "ai", "store"]}, FIXTURES)
        self.assertIn('<span class="l-ext">third party</span>', out)
        self.assertIn('<span class="l-store">datastore</span>', out)
        self.assertNotIn("<span>own component</span>", out)

    def test_own_component_is_available_as_a_type(self):
        out = render_diagram({**TWO_TIER, "legend": ["own", "ext"]}, FIXTURES)
        self.assertIn("<span>own component</span>", out)

    def test_no_legend_key_means_no_legend(self):
        d = {k: v for k, v in TWO_TIER.items() if k != "legend"}
        self.assertNotIn('class="legend"', render_diagram(d, FIXTURES))
