"""个性化健康建议生成（中文 Markdown）。

依据 BMI 分级、体脂率、体重相对健康区间、活动水平与年龄，生成
饮食 / 运动 / 作息三方面的可操作建议，输出 Markdown 文本，
便于在报告页以富文本渲染，也可直接存入数据库与导出。
"""

from calc import BMICategory, Gender, HealthResult


def generate_advice(result: HealthResult, gender: Gender, age: float) -> str:
    cat = result.bmi_category
    bf_label = result.body_fat_label

    out: list = []
    out.append("# 个性化健康建议报告\n")

    # 一、总体评估
    out.append("## 一、总体评估\n")
    out.append(f"- **BMI**：{result.bmi:.1f}（{result.bmi_label}）")
    out.append(f"- **体脂率估算**：{result.body_fat:.1f}%（{bf_label}）")
    out.append(f"- **基础代谢率 (BMR)**：约 {result.bmr:.0f} kcal/天")
    out.append(
        f"- **每日总消耗 (TDEE)**：约 {result.tdee:.0f} kcal/天"
        f"（活动水平：{result.activity_label}）"
    )
    out.append(
        f"- **健康体重区间**：{result.healthy_weight_low:.1f} ~ "
        f"{result.healthy_weight_high:.1f} kg"
    )
    out.append(f"- {result.weight_note}\n")

    # 二、饮食与热量
    out.append("## 二、热量与饮食建议\n")
    if cat == BMICategory.UNDERWEIGHT:
        target = result.tdee + 300
        out.append(
            f"- 目标：适度增重。建议每日摄入约 **{target:.0f} kcal**"
            f"（在消耗基础上 +300）。"
        )
        out.append("- 增加优质蛋白（蛋奶肉鱼、豆制品）与复合碳水（燕麦、薯类、杂粮）。")
        out.append("- 采用少食多餐，避免空腹过久；可适当加餐坚果、酸奶。")
    elif cat == BMICategory.NORMAL:
        target = result.tdee
        out.append(
            f"- 目标：维持健康体重。建议每日摄入约 **{target:.0f} kcal**。"
        )
        out.append("- 保持膳食均衡：谷薯、蛋白、蔬果、健康脂肪比例合理。")
        out.append("- 规律三餐，控制高糖、高油零食与含糖饮料。")
    else:  # 超重 / 肥胖
        target = result.tdee - 500
        out.append(
            f"- 目标：逐步减重。建议每日摄入约 **{target:.0f} kcal**"
            f"（在消耗基础上 -500，约每周减 0.5 kg，安全可持续）。"
        )
        out.append("- 减少精制碳水与添加糖，增加蔬菜、全谷与优质蛋白以提升饱腹感。")
        out.append("- 控制烹调用油与外卖频次，细嚼慢咽、避免暴饮暴食。")
    out.append("")

    # 三、运动
    out.append("## 三、运动建议\n")
    if cat == BMICategory.UNDERWEIGHT:
        out.append(
            "- 以力量 / 抗阻训练为主（每周 3-4 次），促进肌肉合成；"
            "有氧控制在中等强度且不过量。"
        )
    elif cat == BMICategory.NORMAL:
        out.append(
            "- 每周至少 150 分钟中等强度有氧（快走、骑行、游泳）"
            "＋ 2 次力量训练，维持体能与肌肉量。"
        )
    else:
        out.append(
            "- 每周 ≥150 分钟中等强度有氧（快走、慢跑、游泳）"
            "＋ 2-3 次力量训练，循序渐进、避免受伤。"
        )
        out.append(
            "- 可从低强度起步，用每日步数目标（如 6000-8000 步）逐步提升活动量。"
        )
    if "久坐" in result.activity_label:
        out.append("- 您当前偏久坐，建议每坐 1 小时起身活动 3-5 分钟，减少静态时间。")
    out.append("")

    # 四、作息与生活习惯
    out.append("## 四、作息与生活习惯\n")
    out.append("- 保证每晚 7-8 小时睡眠，利于代谢恢复与食欲调节。")
    out.append("- 规律作息、管理压力，避免情绪性进食。")
    if age >= 50:
        out.append(
            "- 年龄 ≥50，建议重视骨密度与肌肉量，适当补充钙与维生素 D，并定期体检。"
        )
    if bf_label in ("偏高", "肥胖"):
        out.append(
            "- 体脂率偏高，内脏脂肪风险上升，建议饮食与运动双管齐下优先改善。"
        )
    out.append("")
    out.append(
        "> 提示：本报告基于通用公式估算，仅供健康参考，不能替代专业医疗诊断。"
    )
    return "\n".join(out)
