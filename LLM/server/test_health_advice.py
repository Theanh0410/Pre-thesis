import unittest

from health_advice import (
    BLOOD_PRESSURE_ADVICE,
    BLOOD_PRESSURE_EMERGENCY_ADVICE,
    classify_blood_pressure,
)


class ClassifyBloodPressureTests(unittest.TestCase):
    def test_missing_reading_returns_none(self):
        self.assertIsNone(classify_blood_pressure(None, 80))
        self.assertIsNone(classify_blood_pressure(120, None))
        self.assertIsNone(classify_blood_pressure(None, None))

    def test_normal(self):
        self.assertEqual(
            classify_blood_pressure(118, 76), {"status": "Normal", "is_emergency": False}
        )

    def test_normal_boundaries(self):
        # Lowest normal and the last values below the "High" thresholds.
        self.assertEqual(classify_blood_pressure(90, 60)["status"], "Normal")
        self.assertEqual(classify_blood_pressure(129, 79)["status"], "Normal")

    def test_high_threshold_on_either_number(self):
        self.assertEqual(classify_blood_pressure(130, 70)["status"], "High")
        self.assertEqual(classify_blood_pressure(120, 80)["status"], "High")

    def test_low_threshold_on_either_number(self):
        self.assertEqual(classify_blood_pressure(89, 70)["status"], "Low")
        self.assertEqual(classify_blood_pressure(110, 59)["status"], "Low")

    def test_emergency_on_either_number(self):
        self.assertEqual(
            classify_blood_pressure(180, 90), {"status": "High", "is_emergency": True}
        )
        self.assertEqual(
            classify_blood_pressure(150, 120), {"status": "High", "is_emergency": True}
        )

    def test_just_below_emergency_is_not_flagged(self):
        self.assertFalse(classify_blood_pressure(179, 119)["is_emergency"])

    def test_every_status_has_advice(self):
        for status in ("Low", "Normal", "High"):
            self.assertTrue(BLOOD_PRESSURE_ADVICE[status])
        self.assertTrue(BLOOD_PRESSURE_EMERGENCY_ADVICE)


if __name__ == "__main__":
    unittest.main()
