"""无显示环境的 UI 冒烟测试（QT_QPA_PLATFORM=offscreen）。

构造完整主窗口、模拟生成跨周报告、切换所有分页、校验周汇总与 CSV 导出，
确保代码可运行、无明显构造/逻辑错误。不依赖显示器。
"""

import os
import sys
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import datetime, timedelta

from PyQt6.QtWidgets import QApplication

import storage
from calc import ActivityLevel, Gender, compute_all
import report_gen

# 使用临时数据库，避免污染用户数据
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
storage.DB_PATH = _tmp.name


def main():
    storage.init_db()
    app = QApplication(sys.argv)

    from ui.main_window import MainWindow

    win = MainWindow()
    win.show()

    now = datetime.now()
    scenarios = [
        (70, 175, 30, Gender.MALE, ActivityLevel.MODERATE, now),
        (82, 175, 30, Gender.MALE, ActivityLevel.SEDENTARY, now),
        (60, 170, 28, Gender.FEMALE, ActivityLevel.LIGHT, now - timedelta(days=10)),
    ]

    ids = []
    for weight, height, age, gender, activity, ts in scenarios:
        result = compute_all(weight, height, age, gender, activity)
        advice = report_gen.generate_advice(result, gender, age)
        rid = storage.save_report(
            result, name="测试", gender=gender, age=age, height=height,
            weight=weight, activity=activity, ts=ts, advice=advice,
        )
        ids.append(rid)

    # 模拟主窗口收到「生成报告」事件，驱动结果/建议/历史/周汇总刷新
    win.on_report_generated(ids[0])
    win.on_history_selected(ids[2])

    # 切换所有分页，构造各页面控件
    for i in range(5):
        win.sidebar.setCurrentRow(i)

    # 校验数据
    reports = storage.list_reports()
    assert len(reports) == 3, f"报告数应为 3，实际 {len(reports)}"

    summaries = storage.get_weekly_summaries()
    assert len(summaries) == 2, f"周汇总应为 2 周，实际 {len(summaries)}"
    print("周汇总行数:", len(summaries))
    for s in summaries:
        print(f"  {s['week_start']} ~ {s['week_end']}  报告数={s['report_count']}  "
              f"平均BMI={s['avg_bmi']} 平均体重={s['avg_weight']}")

    # CSV 导出校验
    rep_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False).name
    wk_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False).name
    storage.export_reports_csv(rep_csv)
    storage.export_weekly_csv(wk_csv)
    assert os.path.getsize(rep_csv) > 0, "历史 CSV 为空"
    assert os.path.getsize(wk_csv) > 0, "周汇总 CSV 为空"

    win.close()
    print("SMOKE TEST PASSED: 主窗口构造、报告生成、分页切换、周汇总与导出均正常。")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print("SMOKE TEST FAILED:", repr(e))
        sys.exit(1)
