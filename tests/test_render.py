"""The renderer turns content into markup, and never leaves a fetchable reference behind."""
import unittest
from pathlib import Path

from tools.render import (e, identity_parts, render, render_bullets, render_byline, render_diagram,
                          render_footer, render_gallery, render_header, render_metrics,
                          render_prose)

ROOT = Path(__file__).resolve().parent.parent

CONTENT = {
    "slug": "demo", "title": "Demo Project",
    "tagline": "A service that does one thing for one team.",
    "chips": [{"label": "Scope", "value": "schema to deploy"}],
    "result": "Cut a two hour task to four minutes.",
    "problem": ["First paragraph.", "Second paragraph."],
    "architecture": ["Walk the request."],
    "diagram": {"mode": "kit", "caption": "One path in, one out.", "legend": False,
                "tiers": [{"label": "Ingest",
                           "nodes": [{"text": "API", "note": "FastAPI", "type": "core"}]}]},
    "decisions": [{"chose": "Namespaces", "over": "a collection per tenant",
                   "because": "isolation becomes a property of the query."}],
    "impact": ["Used by two teams."],
    "gallery": [{"src": "pixel.png", "caption": "What it proves."},
                {"src": "pixel.png", "caption": "What else it proves."}],
    "out_of_scope": ["No auth, the target was one trusted deploy.", "Next: a key per namespace."],
    "footer": {"name": "A Name", "email": "a@b.com", "link": "https://example.com/repo"},
}

FIXTURES = ROOT / "tests" / "fixtures"


class RenderPartsTest(unittest.TestCase):
    def test_escapes_content(self):
        self.assertEqual(e('<b>&"'), "&lt;b&gt;&amp;&quot;")

    def test_header_has_chips_and_a_labelled_result(self):
        out = render_header(CONTENT)
        self.assertIn("<h1>Demo Project</h1>", out)
        self.assertIn('<li class="chip"><b>Scope</b> schema to deploy</li>', out)
        self.assertIn('<span class="label">What is it?</span>', out)
        self.assertIn("Cut a two hour task to four minutes.</p>", out)

    def test_header_carries_the_identity_byline(self):
        """A reader who never scrolls to the footer still knows whose document this is."""
        out = render_header(CONTENT)
        self.assertIn('<p class="byline">', out)
        self.assertIn("A Name", out)
        self.assertLess(out.index('class="byline"'), out.index('class="chips"'))

    def test_prose_puts_pre_before_and_post_after_paragraphs(self):
        out = render_prose("Impact", ["Body."], pre="<!--P-->", post="<!--Q-->")
        self.assertLess(out.index("<!--P-->"), out.index("<p>Body.</p>"))
        self.assertGreater(out.index("<!--Q-->"), out.index("<p>Body.</p>"))

    def test_prose_section_vanishes_when_empty(self):
        self.assertEqual(render_prose("Impact", []), "")


class IdentityTest(unittest.TestCase):
    def test_a_real_url_is_anchored_and_plain_text_is_not(self):
        self.assertIn('<a href="https://example.com/repo">', render_footer(CONTENT["footer"]))
        self.assertIn("<span>repo link</span>",
                      render_footer({"name": "N", "email": "e", "link": "repo link"}))

    def test_byline_and_footer_render_the_same_three_parts(self):
        parts = identity_parts(CONTENT["footer"])
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertIn(part, render_byline(CONTENT["footer"]))
            self.assertIn(part, render_footer(CONTENT["footer"]))


class BulletsTest(unittest.TestCase):
    def test_items_become_a_bulleted_list(self):
        out = render_bullets("Out-of-Scope", ["No auth yet.", "Next: a key per namespace."])
        self.assertIn('<ul class="bullets">', out)
        self.assertEqual(out.count("<li>"), 2)
        self.assertIn("<h2>Out-of-Scope</h2>", out)

    def test_backticks_still_become_code(self):
        self.assertIn("<code>/ask</code>", render_bullets("Out-of-Scope", ["No auth on `/ask`."]))

    def test_section_vanishes_when_empty(self):
        self.assertEqual(render_bullets("Out-of-Scope", []), "")


class GalleryTest(unittest.TestCase):
    def shots(self, n: int):
        return [{"src": "pixel.png", "caption": f"Proof {i}."} for i in range(n)]

    def test_present_image_is_inlined_as_base64(self):
        out = render_gallery([{"src": "pixel.png", "caption": "What it proves."}], FIXTURES)
        self.assertIn('<img src="data:image/png;base64,iVBORw0KGgo', out)
        self.assertIn("<figcaption>What it proves.</figcaption>", out)

    def test_two_and_four_images_get_two_columns(self):
        for n in (2, 4):
            self.assertIn('class="gallery cols2"', render_gallery(self.shots(n), FIXTURES))

    def test_three_and_five_images_get_three_columns(self):
        for n in (3, 5):
            self.assertIn('class="gallery cols3"', render_gallery(self.shots(n), FIXTURES))

    def test_each_image_expands_via_its_own_target(self):
        """No JavaScript: the thumbnail links to its figure and CSS lifts that same img."""
        out = render_gallery(self.shots(3), FIXTURES)
        for i in (1, 2, 3):
            self.assertIn(f'<figure class="shot" id="shot-{i}">', out)
            self.assertIn(f'<a class="zoom" href="#shot-{i}">', out)
        self.assertEqual(out.count('<a class="close" href="#gallery">'), 3)
        self.assertIn('<section id="gallery">', out)

    def test_missing_image_becomes_a_visible_named_placeholder(self):
        """Version 2 hid slots unless the figure was marked missing. The mark is gone."""
        out = render_gallery([{"src": "images/99-nope.png", "caption": "Caption survives."}],
                             FIXTURES)
        self.assertIn('<div class="slot">images/99-nope.png</div>', out)
        self.assertNotIn("missing", out)
        self.assertNotIn("<img", out)
        self.assertIn("Caption survives.", out)

    def test_a_missing_image_is_not_expandable(self):
        out = render_gallery([{"src": "nope.png", "caption": "c"}], FIXTURES)
        self.assertNotIn('class="zoom"', out)

    def test_section_vanishes_without_images(self):
        self.assertEqual(render_gallery([], FIXTURES), "")


class RenderDocumentTest(unittest.TestCase):
    def setUp(self):
        self.doc = render(CONTENT, FIXTURES)

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

    def test_sections_are_in_the_version_three_order(self):
        """Gallery after Impact, so the screenshots read as proof of the claims."""
        headings = ["Problem", "Architecture", "Decisions and tradeoffs", "Impact", "Gallery",
                    "Out-of-Scope"]
        found = [self.doc.index(f"<h2>{h}</h2>") for h in headings]
        self.assertEqual(found, sorted(found), f"order is wrong: {headings}")

    def test_identity_prints_twice(self):
        self.assertEqual(self.doc.count("A Name"), 2)

    def test_no_backgrounds_variant_neutralises_fills(self):
        variant = render(CONTENT, FIXTURES, no_backgrounds=True)
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
        self.out = render_diagram(TWO_TIER, FIXTURES)

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
                         render_diagram({**TWO_TIER, "legend": False}, FIXTURES))

    def test_caption_is_numbered(self):
        self.assertIn("<b>Fig 1.</b> Retrieval is deterministic.", self.out)

    def test_image_mode_missing_file_degrades_to_a_named_slot(self):
        out = render_diagram({"mode": "image", "image": "architecture.png", "caption": "c"},
                             FIXTURES)
        self.assertIn('<div class="slot">architecture.png</div>', out)
        self.assertNotIn("<img", out)


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
