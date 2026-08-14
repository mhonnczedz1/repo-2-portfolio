"""The quality bar is enforced, not advised. Each test breaks exactly one rule."""
import unittest

from tests.helpers import FIXTURES, content
from tools.check import (BUDGETS, TODO, TOTAL, check_banned, check_budgets, check_counts,
                         check_decisions, check_diagram, check_schema, section_texts, warnings,
                         words)


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
        del c["limits"]
        self.assertTrue(any("limits" in x for x in check_schema(c)))

    def test_empty_required_field_fails(self):
        self.assertTrue(any("limits" in x for x in check_schema(content(limits=[]))))

    def test_wrong_type_fails(self):
        self.assertTrue(any("problem" in x for x in check_schema(content(problem="a string"))))


class BudgetTest(unittest.TestCase):
    def test_valid_fixture_is_within_budget(self):
        self.assertEqual(check_budgets(content()), [])

    def test_section_over_its_budget_fails(self):
        c = content(limits=["word " * (BUDGETS["limits"] + 5)])
        self.assertTrue(any("limits" in x for x in check_budgets(c)))

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
