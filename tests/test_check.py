"""The quality bar is enforced, not advised. Each test breaks exactly one rule."""
import unittest

from tests.helpers import content
from tools.check import BUDGETS, TOTAL, check_budgets, check_schema, section_texts, words


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
