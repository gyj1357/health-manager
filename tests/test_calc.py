"""健康指标计算引擎单元测试（headless 运行，无需 GUI）。"""

import math
import unittest

from calc import (
    ActivityLevel,
    BMICategory,
    Gender,
    calculate_bmi,
    classify_bmi,
    calculate_bmr,
    calculate_tdee,
    estimate_body_fat,
    classify_body_fat,
    healthy_weight_range,
    compute_all,
)


class TestBMI(unittest.TestCase):
    def test_bmi_value(self):
        # 70kg / 175cm -> 22.857
        self.assertAlmostEqual(calculate_bmi(70, 175), 70 / 1.75 ** 2, places=3)

    def test_bmi_invalid(self):
        with self.assertRaises(ValueError):
            calculate_bmi(70, 0)
        with self.assertRaises(ValueError):
            calculate_bmi(0, 175)

    def test_classify_boundaries(self):
        self.assertEqual(classify_bmi(18.4)[0], BMICategory.UNDERWEIGHT)
        self.assertEqual(classify_bmi(18.5)[0], BMICategory.NORMAL)
        self.assertEqual(classify_bmi(23.9)[0], BMICategory.NORMAL)
        self.assertEqual(classify_bmi(24.0)[0], BMICategory.OVERWEIGHT)
        self.assertEqual(classify_bmi(27.9)[0], BMICategory.OVERWEIGHT)
        self.assertEqual(classify_bmi(28.0)[0], BMICategory.OBESE)

    def test_classify_colors(self):
        self.assertEqual(classify_bmi(17)[2], "#3498db")
        self.assertEqual(classify_bmi(21)[2], "#27ae60")
        self.assertEqual(classify_bmi(26)[2], "#e67e22")
        self.assertEqual(classify_bmi(30)[2], "#e74c3c")


class TestBMR(unittest.TestCase):
    def test_bmr_male(self):
        # 10*70 + 6.25*175 - 5*30 + 5 = 1648.75
        self.assertAlmostEqual(calculate_bmr(70, 175, 30, Gender.MALE), 1648.75, places=2)

    def test_bmr_female(self):
        # 同上 - 166 = 1482.75
        self.assertAlmostEqual(calculate_bmr(70, 175, 30, Gender.FEMALE), 1482.75, places=2)


class TestTDEE(unittest.TestCase):
    def test_tdee_sedentary(self):
        bmr = calculate_bmr(70, 175, 30, Gender.MALE)
        self.assertAlmostEqual(calculate_tdee(bmr, ActivityLevel.SEDENTARY), bmr * 1.2, places=2)

    def test_tdee_active(self):
        bmr = calculate_bmr(70, 175, 30, Gender.MALE)
        self.assertAlmostEqual(calculate_tdee(bmr, ActivityLevel.ACTIVE), bmr * 1.725, places=2)


class TestBodyFat(unittest.TestCase):
    def test_body_fat_male(self):
        bmi = calculate_bmi(70, 175)  # ~22.857
        # 1.20*22.857 + 0.23*30 - 10.8*1 - 5.4 = 18.128
        expected = 1.20 * bmi + 0.23 * 30 - 10.8 - 5.4
        self.assertAlmostEqual(estimate_body_fat(bmi, 30, Gender.MALE), expected, places=2)

    def test_body_fat_female_higher(self):
        bmi = calculate_bmi(70, 175)
        male = estimate_body_fat(bmi, 30, Gender.MALE)
        female = estimate_body_fat(bmi, 30, Gender.FEMALE)
        self.assertAlmostEqual(female - male, 10.8, places=2)

    def test_classify_body_fat(self):
        self.assertEqual(classify_body_fat(Gender.MALE, 5)[0], "偏低")
        self.assertEqual(classify_body_fat(Gender.MALE, 15)[0], "健康")
        self.assertEqual(classify_body_fat(Gender.MALE, 22)[0], "偏高")
        self.assertEqual(classify_body_fat(Gender.MALE, 30)[0], "肥胖")
        self.assertEqual(classify_body_fat(Gender.FEMALE, 10)[0], "偏低")
        self.assertEqual(classify_body_fat(Gender.FEMALE, 20)[0], "健康")


class TestHealthyWeight(unittest.TestCase):
    def test_range(self):
        low, high = healthy_weight_range(175)
        self.assertAlmostEqual(low, 18.5 * 1.75 ** 2, places=2)
        self.assertAlmostEqual(high, 23.9 * 1.75 ** 2, places=2)
        self.assertTrue(low < high)


class TestComputeAll(unittest.TestCase):
    def test_full_pipeline(self):
        r = compute_all(70, 175, 30, Gender.MALE, ActivityLevel.MODERATE)
        self.assertAlmostEqual(r.bmi, 70 / 1.75 ** 2, places=3)
        self.assertEqual(r.bmi_category, BMICategory.NORMAL)
        self.assertAlmostEqual(r.tdee, r.bmr * 1.55, places=2)
        self.assertTrue(r.healthy_weight_low < 70 < r.healthy_weight_high)
        self.assertIn("健康范围", r.weight_note)

    def test_overweight_note(self):
        # 80kg / 170cm -> BMI ≈ 27.68，属超重
        r = compute_all(80, 170, 40, Gender.MALE, ActivityLevel.SEDENTARY)
        self.assertEqual(r.bmi_category, BMICategory.OVERWEIGHT)
        self.assertIn("高于健康范围", r.weight_note)

    def test_obese_category(self):
        # 90kg / 170cm -> BMI ≈ 31.14，属肥胖
        r = compute_all(90, 170, 40, Gender.MALE, ActivityLevel.SEDENTARY)
        self.assertEqual(r.bmi_category, BMICategory.OBESE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
