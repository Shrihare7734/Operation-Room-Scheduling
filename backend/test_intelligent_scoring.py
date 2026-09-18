import unittest
from datetime import datetime, timedelta

from intelligent_scoring import ContextDetector, ScoringEngine
from scheduler import validate_time_window


class IntelligentScoringTests(unittest.TestCase):
    def test_priority_scores_are_bounded(self):
        engine = ScoringEngine()
        scores = [engine.calculate_priority_score(value) for value in ("emergency", "urgent", "routine", "elective")]
        self.assertEqual(scores, [100, 75, 50, 25])
        self.assertTrue(all(0 <= score <= 100 for score in scores))

    def test_context_profiles_have_expected_multipliers(self):
        detector = ContextDetector()
        self.assertEqual(detector.get_weights_for_context("EMERGENCY_SURGE")["context_multiplier"], 1.5)
        self.assertEqual(detector.get_weights_for_context("RESOURCE_SHORTAGE")["equipment"], 30)

    def test_invalid_window_is_rejected(self):
        start = datetime.now()
        procedure = {
            "earliest_start_time": start.isoformat(),
            "latest_end_time": (start + timedelta(minutes=15)).isoformat(),
        }
        self.assertIn("at least 30 minutes", validate_time_window(procedure)[0])


if __name__ == "__main__":
    unittest.main()