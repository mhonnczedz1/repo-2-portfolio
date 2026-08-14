"""The skill's documentation must not drift from the code that enforces it."""
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.check import (BANNED, BUDGETS, TOTAL, check_banned, check_counts, check_decisions,
                         check_diagram, check_schema)
from tools.svgcheck import check_svg, svg_words

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / ".claude" / "skills" / "project-overview"
TEMPLATE = SKILL / "references" / "architecture-template.svg"


def skill_text() -> str:
    return (SKILL / "SKILL.md").read_text(encoding="utf-8")


class FrontmatterTest(unittest.TestCase):
    def test_frontmatter_declares_name_and_description(self):
        head = skill_text().split("---")[1]
        self.assertIn("name: project-overview", head)
        self.assertRegex(head, r"description: \S")

    def test_description_is_one_line(self):
        head = skill_text().split("---")[1]
        desc = re.search(r"description: (.*)", head).group(1)
        self.assertGreater(len(desc), 80, "too vague to trigger reliably")

    def test_referenced_files_exist(self):
        for name in re.findall(r"`references/([\w.-]+)`", skill_text()):
            self.assertTrue((SKILL / "references" / name).is_file(), name)


class BudgetTableTest(unittest.TestCase):
    """The table in SKILL.md is a guide, but a stale one would mislead."""

    def test_every_budget_in_the_table_matches_the_validator(self):
        rows = re.findall(r"^\| ([A-Z][^|]+?) \| (\d+) \|", skill_text(), re.M)
        self.assertEqual(len(rows), len(BUDGETS), f"expected {len(BUDGETS)} budget rows, {rows}")
        self.assertEqual(sorted(int(n) for _, n in rows), sorted(BUDGETS.values()))

    def test_hard_limit_is_stated_correctly(self):
        self.assertIn(f"{TOTAL} printed words hard", skill_text())

    def test_budgeted_total_matches_the_sum(self):
        self.assertIn(f"{sum(BUDGETS.values())} budgeted", skill_text())


class BannedWordTest(unittest.TestCase):
    def test_skill_lists_every_banned_word(self):
        listed = re.search(r"Banned words[^\n]*:(.*?)\.", skill_text(), re.S).group(1)
        for word in ("robust", "seamless", "cutting-edge", "leverage", "utilize"):
            self.assertIn(word, listed)
            self.assertTrue(BANNED.search(word), f"{word} documented but not enforced")


class ExampleTest(unittest.TestCase):
    """The content.json example in SKILL.md is what an agent will copy. It must be valid."""

    def setUp(self):
        block = re.search(r"```json\n(.*?)```", skill_text(), re.S).group(1)
        self.example = json.loads(block)
        # The example points at images/architecture.svg, the path a real overview uses, so stage
        # the shipped template there. That makes the diagram check resolve against a real file
        # and, since check_diagram now verifies SVG geometry, checks the template at the same time.
        self.base = Path(tempfile.mkdtemp())
        (self.base / "images").mkdir()
        shutil.copy(TEMPLATE, self.base / "images" / "architecture.svg")
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)

    def test_example_satisfies_the_schema(self):
        self.assertEqual(check_schema(self.example), [])

    def test_example_breaks_no_quality_rule(self):
        c = self.example
        self.assertEqual(check_banned(c) + check_decisions(c) + check_counts(c), [])
        self.assertEqual(check_diagram(c, self.base), [])

    def test_example_diagram_is_valid_in_whichever_mode_it_declares(self):
        """Holds for both modes, since the example may legitimately show either."""
        d = self.example["diagram"]
        if d.get("mode") == "image":
            self.assertTrue(d["image"].endswith((".svg", ".png")), d["image"])
        else:
            kinds = {n.get("type") for tier in d["tiers"] for n in tier["nodes"]}
            self.assertTrue(kinds <= {None, "core", "ext", "store", "ai"}, kinds)


class FlowTemplateTest(unittest.TestCase):
    """The template is shipped to be copied, so it has to be correct on its own."""

    FLOW_DOC = SKILL / "references" / "diagram-flow.md"

    def test_geometry_holds(self):
        self.assertEqual(check_svg(TEMPLATE), [])

    def test_it_leaves_room_for_a_caption(self):
        spent = sum(len(t.split()) for t in svg_words(TEMPLATE))
        self.assertLess(spent, BUDGETS["diagram"] - 10,
                        "a template that fills the diagram budget leaves nothing for the caption")

    def test_it_carries_no_legend(self):
        printed = " ".join(svg_words(TEMPLATE)).lower()
        for phrase in ("third party", "model step", "outside the app", "own component"):
            self.assertNotIn(phrase, printed, "flow diagrams carry no legend")

    def test_canvas_ceiling_matches_the_documented_one(self):
        width = float(re.search(r'viewBox="0 0 ([\d.]+)', TEMPLATE.read_text(encoding="utf-8"))
                      .group(1))
        self.assertLessEqual(width, 660, "wider than 660px overflows the A4 text column")
        self.assertIn("660", self.FLOW_DOC.read_text(encoding="utf-8"))
