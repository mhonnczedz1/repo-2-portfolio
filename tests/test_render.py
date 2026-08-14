"""The renderer turns content into markup, and never leaves a fetchable reference behind."""
import unittest
from pathlib import Path

from tools.render import e, render, render_diagram, render_footer, render_header, render_prose

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
