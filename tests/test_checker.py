import unittest

import cases
import checker


def case_by_id(case_id: str) -> dict:
    return next(case for case in cases.CASES if case["case_id"] == case_id)


class NumericFieldValidationTest(unittest.TestCase):
    def test_whole_number_strings_still_pass(self):
        self.assertTrue(checker.check_quantity("30", 30)["correct"])
        self.assertTrue(checker.check_days_supply("7", 7)["correct"])
        self.assertTrue(checker.check_refills("5", 5)["correct"])
        self.assertTrue(checker.check_daw("1", 1)["correct"])

    def test_decimal_inputs_do_not_truncate_to_correct_values(self):
        checks = [
            checker.check_quantity("1.9", 1),
            checker.check_days_supply("30.9", 30),
            checker.check_refills("5.5", 5),
            checker.check_daw("1.9", 1),
        ]

        for result in checks:
            with self.subTest(result=result):
                self.assertFalse(result["correct"])
                self.assertIn("whole number", result["explanation"])


class SigValidationTest(unittest.TestCase):
    def test_incomplete_prn_indication_does_not_pass(self):
        examples = [
            ("rx_010", "Take 1 tablet by mouth every 6 hours as needed"),
            ("rx_020", "Take 2 tablets by mouth every 6 hours as needed"),
            ("rx_027", "Inhale 2 puffs by inhalation every 6 hours as needed"),
        ]

        for case_id, sig in examples:
            case = case_by_id(case_id)
            result = checker.check_sig(sig, case["expected"]["sig_components"])
            with self.subTest(case_id=case_id):
                self.assertFalse(result["correct"])
                self.assertIn("indication", result["explanation"])

    def test_incomplete_food_or_meal_modifier_does_not_pass(self):
        examples = [
            ("rx_017", "Take 1 tablet by mouth twice daily"),
            ("rx_019", "Take 1 tablet by mouth three times daily"),
        ]

        for case_id, sig in examples:
            case = case_by_id(case_id)
            result = checker.check_sig(sig, case["expected"]["sig_components"])
            with self.subTest(case_id=case_id):
                self.assertFalse(result["correct"])
                self.assertIn("food_or_meal", result["explanation"])

    def test_complete_required_sig_meanings_still_pass(self):
        examples = [
            ("rx_010", "Take one tablet orally every 6 hours if needed for pain"),
            ("rx_017", "Take one tablet orally twice a day with food"),
            (
                "rx_027",
                "Inhale two puffs by inhalation every six hours as needed "
                "for shortness of breath",
            ),
        ]

        for case_id, sig in examples:
            case = case_by_id(case_id)
            result = checker.check_sig(sig, case["expected"]["sig_components"])
            with self.subTest(case_id=case_id):
                self.assertTrue(result["correct"])

    def test_canonical_case_answers_still_pass(self):
        failures = []
        for case in cases.CASES:
            expected = case["expected"]
            answers = {
                "drug_name": expected["drug_name"],
                "strength": expected["strength"],
                "quantity": expected["quantity"],
                "sig": expected.get("sig_english", ""),
                "days_supply": expected["days_supply"],
                "refills": expected["refills"],
                "daw": expected["daw"],
            }
            results = checker.check_all(answers, expected, case.get("extras"))
            misses = [
                field for field, result in results.items()
                if not result["correct"]
            ]
            if misses:
                failures.append((case["case_id"], misses))

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
