"""The quality bar is enforced, not advised. Each test breaks exactly one rule."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, content
from tools.check import (BUDGETS, TODO, TOTAL, check_banned, check_budgets, check_counts,
                         check_decisions, check_diagram, check_output, check_schema, main,
                         section_texts, warnings, words)

ROOT = Path(__file__).resolve().parent.parent


class WordCountTest(unittest.TestCase):
    def test_counts_words(self):
        self.assertEqual(words("one two", "three"), 3)

    def test_todo_marker_itself_is_not_a_word(self):
        self.assertEqual(words("TODO(verify) documents ingested"), 2)

    def test_every_budgeted_section_is_counted(self):
        self.assertEqual(set(section_texts(content())), set(BUDGETS))

    def test_diagram_labels_and_notes_count_towards_the_diagram_budget(self):
        c = content()
        c["diagram"]["tiers"][0]["nodes"][0]["note"] = "one two three four five"
        before = words(*section_texts(content())["diagram"])
        after = words(*section_texts(c)["diagram"])
        self.assertGreater(after, before)


class SchemaTest(unittest.TestCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(check_schema(content()), [])

    def test_missing_required_field_fails(self):
        c = content()
        del c["out_of_scope"]
        self.assertTrue(any("out_of_scope" in x for x in check_schema(c)))

    def test_empty_required_field_fails(self):
        self.assertTrue(any("out_of_scope" in x for x in check_schema(content(out_of_scope=[]))))

    def test_wrong_type_fails(self):
        self.assertTrue(any("problem" in x for x in check_schema(content(problem="a string"))))


class BudgetTest(unittest.TestCase):
    def test_valid_fixture_is_within_budget(self):
        self.assertEqual(check_budgets(content()), [])

    def test_section_over_its_budget_fails(self):
        c = content(out_of_scope=["word " * (BUDGETS["out_of_scope"] + 5)])
        self.assertTrue(any("out_of_scope" in x for x in check_budgets(c)))

    def test_total_over_the_hard_limit_fails(self):
        c = content(architecture=["word " * 400])
        self.assertTrue(any(str(TOTAL) in x for x in check_budgets(c)))


class QualityBarTest(unittest.TestCase):
    def test_valid_fixture_trips_nothing(self):
        c = content()
        self.assertEqual(check_banned(c) + check_decisions(c) + check_counts(c), [])
        self.assertEqual(check_diagram(c, FIXTURES), [])

    def test_banned_superlative_fails_anywhere(self):
        self.assertTrue(check_banned(content(impact=["A robust and seamless pipeline."])))

    def test_banned_words_are_stem_matched(self):
        self.assertTrue(check_banned(content(impact=["We leveraged the index."])))
        self.assertTrue(check_banned(content(impact=["Robustness was the goal."])))

    def test_banned_word_in_a_node_label_fails(self):
        c = content()
        c["diagram"]["tiers"][0]["nodes"][0]["note"] = "utilizes Redis"
        self.assertTrue(check_banned(c))

    def test_decision_without_a_rejected_alternative_fails(self):
        c = content()
        del c["decisions"][0]["over"]
        self.assertTrue(any("over" in x for x in check_decisions(c)))

    def test_decision_with_an_empty_reason_fails(self):
        c = content()
        c["decisions"][0]["because"] = "  "
        self.assertTrue(any("because" in x for x in check_decisions(c)))

    def test_thirteen_nodes_fails(self):
        c = content()
        c["diagram"]["tiers"][0]["nodes"] = [{"text": f"N{i}"} for i in range(13)]
        self.assertTrue(any("12" in x for x in check_diagram(c, FIXTURES)))

    def test_two_core_nodes_fails(self):
        c = content()
        for tier in c["diagram"]["tiers"]:
            for n in tier["nodes"]:
                n["type"] = "core"
        self.assertTrue(any("core" in x for x in check_diagram(c, FIXTURES)))

    def test_no_core_node_fails(self):
        c = content()
        for tier in c["diagram"]["tiers"]:
            for n in tier["nodes"]:
                n.pop("type", None)
        self.assertTrue(any("core" in x for x in check_diagram(c, FIXTURES)))

    def test_unknown_node_type_fails(self):
        c = content()
        c["diagram"]["tiers"][0]["nodes"][0]["type"] = "database"
        self.assertTrue(any("database" in x for x in check_diagram(c, FIXTURES)))

    def test_one_tier_fails(self):
        c = content()
        c["diagram"]["tiers"] = c["diagram"]["tiers"][:1]
        self.assertTrue(any("tier" in x for x in check_diagram(c, FIXTURES)))

    def test_image_mode_with_a_missing_file_fails(self):
        c = content(diagram={"mode": "image", "image": "nope.png", "caption": "c"})
        self.assertTrue(any("nope.png" in x for x in check_diagram(c, FIXTURES)))

    def test_six_chips_fails(self):
        c = content(chips=[{"label": f"L{i}", "value": "v"} for i in range(6)])
        self.assertTrue(any("chips" in x for x in check_counts(c)))

    def test_a_single_metric_fails(self):
        c = content(metrics=[{"value": "1", "label": "lonely"}])
        self.assertTrue(any("metrics" in x for x in check_counts(c)))

    def test_no_metrics_at_all_is_fine(self):
        c = content()
        del c["metrics"]
        self.assertEqual(check_counts(c), [])


class GalleryTest(unittest.TestCase):
    """2 to 5 images, one sentence each. Counts are enforced now, not advised."""

    def shots(self, n: int):
        return [{"src": "pixel.png", "caption": f"Proof number {i}."} for i in range(n)]

    def test_two_to_five_images_pass(self):
        for n in (2, 3, 4, 5):
            self.assertEqual(check_counts(content(gallery=self.shots(n))), [], f"{n} images")

    def test_no_gallery_at_all_is_fine(self):
        c = content()
        del c["gallery"]
        self.assertEqual(check_counts(c), [])

    def test_a_single_image_fails(self):
        self.assertTrue(any("gallery" in x for x in check_counts(content(gallery=self.shots(1)))))

    def test_six_images_fails(self):
        self.assertTrue(any("gallery" in x for x in check_counts(content(gallery=self.shots(6)))))

    def test_a_caption_of_fourteen_words_passes(self):
        cap = " ".join(["word"] * 13) + " end."
        self.assertEqual(check_counts(content(gallery=[{"src": "a.png", "caption": cap},
                                                       {"src": "b.png", "caption": "Short."}])), [])

    def test_a_caption_of_fifteen_words_fails(self):
        cap = " ".join(["word"] * 14) + " end."
        errors = check_counts(content(gallery=[{"src": "a.png", "caption": cap},
                                               {"src": "b.png", "caption": "Short."}]))
        self.assertTrue(any("caption" in x for x in errors), errors)

    def test_the_fifty_word_pool_is_what_limits_five_images(self):
        """Five captions at the 14 word cap would be 70, so the pool still binds."""
        cap = " ".join(["word"] * 13) + " end."
        c = content(gallery=[{"src": f"{i}.png", "caption": cap} for i in range(5)])
        self.assertTrue(any("gallery" in x for x in check_budgets(c)))


class IdentityBudgetTest(unittest.TestCase):
    def test_identity_is_counted_twice_because_it_prints_twice(self):
        f = content()["footer"]
        once = words(f["name"], f["email"], f["link"])
        self.assertEqual(words(*section_texts(content())["identity"]), once * 2)


class WarningTest(unittest.TestCase):
    def test_outstanding_todo_warns_but_does_not_fail(self):
        self.assertTrue(any("TODO" in w for w in warnings(content(impact=[f"Adoption {TODO}"]))))

    def test_five_decisions_warns(self):
        c = content()
        c["decisions"] = c["decisions"][:1] * 5
        self.assertTrue(any("decisions" in w for w in warnings(c)))

    def test_a_tier_of_one_node_warns(self):
        c = content()
        c["diagram"]["tiers"][0]["nodes"] = [{"text": "Alone", "type": "core"}]
        for tier in c["diagram"]["tiers"][1:]:
            for n in tier["nodes"]:
                n.pop("type", None)
        self.assertTrue(any("tier" in w for w in warnings(c)))


class OutputTest(unittest.TestCase):
    def _write(self, body: str) -> Path:
        path = ROOT / "out" / "test-selfcontained.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        self.addCleanup(path.unlink)
        return path

    def test_clean_output_passes(self):
        path = self._write('<html><body><a href="https://example.com">repo</a>'
                           '<img src="data:image/png;base64,AAA"></body></html>')
        self.assertEqual(check_output(path), [])

    def test_remote_image_fails(self):
        path = self._write('<img src="https://cdn.example.com/a.png">')
        self.assertTrue(any("src" in x for x in check_output(path)))

    def test_stylesheet_link_fails(self):
        path = self._write('<link rel="stylesheet" href="style.css">')
        self.assertTrue(any("link" in x.lower() for x in check_output(path)))

    def test_css_import_fails(self):
        path = self._write("<style>@import url(other.css);</style>")
        self.assertTrue(any("import" in x.lower() for x in check_output(path)))

    def test_remote_url_in_css_fails(self):
        path = self._write("<style>body{ background:url(https://x.test/a.png) }</style>")
        self.assertTrue(any("url" in x.lower() for x in check_output(path)))

    def test_an_anchor_to_a_repo_is_allowed(self):
        path = self._write('<a href="https://github.com/me/proj">source</a>')
        self.assertEqual(check_output(path), [])


class CliTest(unittest.TestCase):
    """overviews/ is gitignored and generated, so the CLI test brings its own content."""

    SLUG = "cli-test-overview"

    def setUp(self):
        base = ROOT / "overviews" / self.SLUG
        base.mkdir(parents=True, exist_ok=True)
        src = base / "content.json"
        src.write_text(json.dumps(content()), encoding="utf-8")
        self.addCleanup(lambda: (src.unlink(missing_ok=True), base.rmdir()))

    def _run(self, *argv) -> tuple:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main([*argv])
        return code, buf.getvalue()

    def test_a_valid_overview_passes(self):
        code, out = self._run(self.SLUG)
        self.assertEqual(code, 0, out)
        self.assertIn("architecture", out)

    def test_strict_mode_fails_on_outstanding_todos(self):
        code, out = self._run(self.SLUG, "--strict")
        self.assertEqual(code, 1)
        self.assertIn("TODO", out)

    def test_unknown_slug_is_an_error_not_a_crash(self):
        code, _ = self._run("no-such-project")
        self.assertEqual(code, 1)


class FlowDiagramTest(unittest.TestCase):
    """A flow diagram is an SVG, so its labels print and its geometry is hand-authored.

    Both were invisible to the validator before: an image-mode diagram was scored on its
    caption alone, and nothing looked inside the file at all.
    """

    FLOW = {"mode": "image", "image": "flow.svg", "caption": "What to notice."}

    def test_svg_labels_count_towards_the_diagram_budget(self):
        c = content(diagram=self.FLOW)
        caption_only = words(*section_texts(c)["diagram"])
        with_labels = words(*section_texts(c, FIXTURES)["diagram"])
        self.assertEqual(caption_only, 3)
        self.assertEqual(with_labels, 9, "PATH client upload API FastAPI write, plus the caption")

    def test_a_png_diagram_is_unaffected(self):
        c = content(diagram={"mode": "image", "image": "pixel.png", "caption": "What to notice."})
        self.assertEqual(words(*section_texts(c, FIXTURES)["diagram"]), 3)

    def test_a_flow_diagram_within_budget_passes(self):
        c = content(diagram=self.FLOW)
        self.assertEqual(check_diagram(c, FIXTURES), [])
        self.assertEqual(check_budgets(c, FIXTURES), [])

    def test_labels_pushing_the_diagram_over_budget_fail(self):
        c = content(diagram={**self.FLOW, "caption": "word " * BUDGETS["diagram"]})
        self.assertTrue(any("diagram" in x for x in check_budgets(c, FIXTURES)))

    def test_broken_geometry_fails_the_build(self):
        broken = Path(tempfile.mkdtemp())
        (broken / "flow.svg").write_text(
            (FIXTURES / "flow.svg").read_text(encoding="utf-8")
            .replace("upload", "upload a document and wait for the embedding call"),
            encoding="utf-8")
        c = content(diagram=self.FLOW)
        self.assertTrue(any("overflows" in x for x in check_diagram(c, broken)))

    def test_a_banned_word_inside_the_svg_fails(self):
        tainted = Path(tempfile.mkdtemp())
        (tainted / "flow.svg").write_text(
            (FIXTURES / "flow.svg").read_text(encoding="utf-8").replace(">upload<", ">robust<"),
            encoding="utf-8")
        c = content(diagram=self.FLOW)
        self.assertTrue(any("robust" in x for x in check_banned(c, tainted)))
