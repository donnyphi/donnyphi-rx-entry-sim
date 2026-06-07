"""Deterministic integrity coverage for Workflow Scenarios.

Validates the shape of every scenario in ``app.SCENARIOS`` and confirms the
scenario renderer runs without crashing under a lightweight, non-browser stub.
These tests do not change app behavior or scenario data.
"""
import unittest

from tests._support import load_app, make_state

app = load_app()

REQUIRED_KEYS = {
    "id", "title", "situation", "context", "options",
    "best_index", "explanation", "escalation",
}


class ScenarioDataIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.scenarios = app.SCENARIOS

    def test_has_a_reasonable_number_of_scenarios(self):
        self.assertGreaterEqual(len(self.scenarios), 5)

    def test_ids_are_unique(self):
        ids = [s["id"] for s in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields_present(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario.get("id")):
                missing = REQUIRED_KEYS - set(scenario.keys())
                self.assertEqual(set(), missing, f"missing fields: {missing}")

    def test_option_count_is_three_or_four_and_nonempty(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertIn(len(scenario["options"]), (3, 4))
                for option in scenario["options"]:
                    self.assertTrue(str(option).strip())

    def test_best_index_in_range(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                best = scenario["best_index"]
                self.assertIsInstance(best, int)
                self.assertGreaterEqual(best, 0)
                self.assertLess(best, len(scenario["options"]))

    def test_explanation_and_escalation_present(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(str(scenario["explanation"]).strip())
                self.assertTrue(str(scenario["escalation"]).strip())

    def test_context_is_nonempty_label_value_pairs(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertGreaterEqual(len(scenario["context"]), 1)
                for pair in scenario["context"]:
                    self.assertEqual(len(pair), 2)
                    label, value = pair
                    self.assertTrue(str(label).strip())
                    self.assertTrue(str(value).strip())

    def test_titles_and_situations_nonempty(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(str(scenario["title"]).strip())
                self.assertTrue(str(scenario["situation"]).strip())


class ScenarioRenderSmokeTest(unittest.TestCase):
    """Lightweight non-browser check that the renderer does not crash."""

    @staticmethod
    def _state(scenario, submitted, choice):
        return make_state(
            scenario_id=scenario["id"],
            scenario_submitted=submitted,
            scenario_choice=choice,
            scenario_attempted_ids=set(),
            scenario_correct_ids=set(),
        )

    def test_render_unsubmitted_does_not_crash(self):
        first = app.SCENARIOS[0]
        app.st.session_state = self._state(first, False, None)
        app.render_workflow_scenarios_section()

    def test_render_after_submit_does_not_crash(self):
        for scenario in app.SCENARIOS:
            with self.subTest(scenario=scenario["id"]):
                app.st.session_state = self._state(
                    scenario, True, scenario["best_index"]
                )
                app.render_workflow_scenarios_section()


if __name__ == "__main__":
    unittest.main()
