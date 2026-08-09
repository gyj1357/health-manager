"""每周健康汇总面板：按自然周聚合历史报告的表格，支持刷新与导出。"""

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import storage


class WeeklyPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("每周健康汇总")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        hint = QLabel(
            "系统会在启动时自动按自然周（周一至周日）汇总历史报告；也可手动刷新或导出 CSV。"
        )
        hint.setObjectName("cardSub")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["周起始", "周结束", "报告数", "平均BMI", "平均体重(kg)",
             "平均BMR", "平均TDEE", "生成时间"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("生成 / 刷新周汇总")
        self.refresh_btn.setObjectName("primaryBtn")
        self.refresh_btn.clicked.connect(self._refresh_summary)
        self.export_btn = QPushButton("导出 CSV")
        self.export_btn.clicked.connect(self._export)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh(self):
        rows = storage.get_weekly_summaries()
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["week_start"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["week_end"]))
            self.table.setItem(i, 2, QTableWidgetItem(str(r["report_count"])))
            self.table.setItem(i, 3, QTableWidgetItem(f'{r["avg_bmi"]:.1f}'))
            self.table.setItem(i, 4, QTableWidgetItem(f'{r["avg_weight"]:.1f}'))
            self.table.setItem(i, 5, QTableWidgetItem(f'{r["avg_bmr"]:.0f}'))
            self.table.setItem(i, 6, QTableWidgetItem(f'{r["avg_tdee"]:.0f}'))
            self.table.setItem(i, 7, QTableWidgetItem(r["generated_at"].replace("T", " ")))
        self.table.resizeColumnsToContents()

    def _refresh_summary(self):
        storage.ensure_weekly_summaries(force=True)
        self.refresh()
        QMessageBox.information(self, "已完成", "周汇总已生成 / 刷新。")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出周汇总", "weekly_summary.csv", "CSV (*.csv)"
        )
        if path:
            storage.export_weekly_csv(path)
            QMessageBox.information(self, "已导出", f"周汇总已导出至：\n{path}")
