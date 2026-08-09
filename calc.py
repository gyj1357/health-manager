"""健康指标计算引擎（纯函数，中国成人标准）。

所有计算均为无副作用的纯函数，便于单元测试与复用。
采用中国成人 BMI 分级标准：偏瘦 <18.5，正常 18.5~23.9，超重 24~27.9，肥胖 ≥28。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"        # 久坐（几乎不运动）
    LIGHT = "light"                # 轻度活动（每周 1-3 天）
    MODERATE = "moderate"          # 中度活动（每周 3-5 天）
    ACTIVE = "active"              # 高度活动（每周 6-7 天）
    VERY_ACTIVE = "very_active"    # 极高活动（体力劳动 / 专业训练）


# 活动系数（Harris/Benedict 修订版常用取值）
ACTIVITY_FACTORS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

ACTIVITY_LABELS_ZH = {
    ActivityLevel.SEDENTARY: "久坐（很少运动）",
    ActivityLevel.LIGHT: "轻度活动（每周 1-3 天）",
    ActivityLevel.MODERATE: "中度活动（每周 3-5 天）",
    ActivityLevel.ACTIVE: "高度活动（每周 6-7 天）",
    ActivityLevel.VERY_ACTIVE: "极高活动（体力劳动/专业训练）",
}

# BMI 分级配色（用于 UI 徽章）
COLOR_UNDERWEIGHT = "#3498db"  # 蓝
COLOR_NORMAL = "#27ae60"       # 绿
COLOR_OVERWEIGHT = "#e67e22"   # 橙
COLOR_OBESE = "#e74c3c"        # 红


class BMICategory(str, Enum):
    UNDERWEIGHT = "underweight"
    NORMAL = "normal"
    OVERWEIGHT = "overweight"
    OBESE = "obese"


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """BMI = 体重(kg) / 身高(m)^2。"""
    if height_cm <= 0:
        raise ValueError("身高必须大于 0")
    if weight_kg <= 0:
        raise ValueError("体重必须大于 0")
    h = height_cm / 100.0
    return weight_kg / (h * h)


def classify_bmi(bmi: float) -> Tuple[BMICategory, str, str]:
    """返回 (分类, 中文标签, 配色)。"""
    if bmi < 18.5:
        return BMICategory.UNDERWEIGHT, "偏瘦", COLOR_UNDERWEIGHT
    if bmi < 24.0:
        return BMICategory.NORMAL, "正常", COLOR_NORMAL
    if bmi < 28.0:
        return BMICategory.OVERWEIGHT, "超重", COLOR_OVERWEIGHT
    return BMICategory.OBESE, "肥胖", COLOR_OBESE


def calculate_bmr(weight_kg: float, height_cm: float, age: float, gender: Gender) -> float:
    """基础代谢率（Mifflin-St Jeor 公式）。"""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender == Gender.MALE else base - 161


def calculate_tdee(bmr: float, activity: ActivityLevel) -> float:
    """每日总能量消耗 = BMR × 活动系数。"""
    return bmr * ACTIVITY_FACTORS[activity]


def estimate_body_fat(bmi: float, age: float, gender: Gender) -> float:
    """体脂率估算（Deurenberg 公式）。

    BF% = 1.20×BMI + 0.23×Age − 10.8×Sex − 5.4  （男 Sex=1，女 Sex=0）
    """
    sex = 1 if gender == Gender.MALE else 0
    return 1.20 * bmi + 0.23 * age - 10.8 * sex - 5.4


def classify_body_fat(gender: Gender, bf: float) -> Tuple[str, str]:
    """体脂率分级，返回 (中文标签, 配色)。简化成人分级。"""
    if gender == Gender.MALE:
        if bf < 6:
            return "偏低", COLOR_UNDERWEIGHT
        if bf < 18:
            return "健康", COLOR_NORMAL
        if bf < 25:
            return "偏高", COLOR_OVERWEIGHT
        return "肥胖", COLOR_OBESE
    else:
        if bf < 14:
            return "偏低", COLOR_UNDERWEIGHT
        if bf < 25:
            return "健康", COLOR_NORMAL
        if bf < 32:
            return "偏高", COLOR_OVERWEIGHT
        return "肥胖", COLOR_OBESE


def healthy_weight_range(height_cm: float) -> Tuple[float, float]:
    """健康体重区间（BMI 18.5 ~ 23.9）。"""
    h = height_cm / 100.0
    return 18.5 * h * h, 23.9 * h * h


@dataclass
class HealthResult:
    bmi: float
    bmi_category: BMICategory
    bmi_label: str
    bmi_color: str
    bmr: float
    tdee: float
    activity_label: str
    body_fat: float
    body_fat_label: str
    body_fat_color: str
    healthy_weight_low: float
    healthy_weight_high: float
    weight_note: str


def compute_all(
    weight_kg: float,
    height_cm: float,
    age: float,
    gender: Gender,
    activity: ActivityLevel,
) -> HealthResult:
    """综合计算所有健康指标。"""
    bmi = calculate_bmi(weight_kg, height_cm)
    cat, label, color = classify_bmi(bmi)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity)
    bf = estimate_body_fat(bmi, age, gender)
    bf_label, bf_color = classify_body_fat(gender, bf)
    low, high = healthy_weight_range(height_cm)

    if weight_kg < low:
        note = "当前体重低于健康范围，建议在保证营养的前提下适度增重。"
    elif weight_kg > high:
        note = "当前体重高于健康范围，建议通过饮食与运动逐步减重。"
    else:
        note = "当前体重处于健康范围，请继续保持良好的生活习惯。"

    return HealthResult(
        bmi=bmi,
        bmi_category=cat,
        bmi_label=label,
        bmi_color=color,
        bmr=bmr,
        tdee=tdee,
        activity_label=ACTIVITY_LABELS_ZH[activity],
        body_fat=bf,
        body_fat_label=bf_label,
        body_fat_color=bf_color,
        healthy_weight_low=low,
        healthy_weight_high=high,
        weight_note=note,
    )
