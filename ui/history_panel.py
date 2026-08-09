"""历史报告记录面板：按时间列出每次生成的报告，点击可查看详情。"""

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal

import storage


class HistoryPanel(QWidget):
    report_selected = pyqtSignal(int)
    generate_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._ids: list = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("历史报告记录")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        hint = QLabel("每次生成报告都会记录时间。点击任意一行可查看该次详细指标与建议。")
        hint.setObjectName("cardSub")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["生成时间", "姓名", "性别", "年龄", "身高(cm)", "体重(kg)", "BMI", "分类"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._on_click)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        self.new_btn = QPushButton("+ 新建报告")
        self.new_btn.setObjectName("primaryBtn")
        self.new_btn.clicked.connect(self.generate_requested.emit)
        self.export_btn = QPushButton("导出 CSV")
        self.export_btn.clicked.connect(self._export)
        btn_row.addWidget(self.new_btn)
        btn_row.addWidget(self.export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def refresh(self):
        rows = storage.list_reports()
        self._ids = [r["id"] for r in rows]
        self.table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(r["ts"].replace("T", " ")))
            self.table.setItem(i, 1, QTableWidgetItem(r["name"] or "—"))
            self.table.setItem(i, 2, QTableWidgetItem("男" if r["gender"] == "male" else "女"))
            self.table.setItem(i, 3, QTableWidgetItem(f'{r["age"]:.0f}'))
            self.table.setItem(i, 4, QTableWidgetItem(f'{r["height"]:.0f}'))
            self.table.setItem(i, 5, QTableWidgetItem(f'{r["weight"]:.1f}'))
            self.table.setItem(i, 6, QTableWidgetItem(f'{r["bmi"]:.1f}'))
            self.table.setItem(i, 7, QTableWidgetItem(r["bmi_label"]))
        self.table.resizeColumnsToContents()

    def _on_click(self, row: int, _col: int):
        if 0 <= row < len(self._ids):
            self.report_selected.emit(self._ids[row])

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出历史报告", "reports.csv", "CSV (*.csv)"
        )
        if path:
            storage.export_reports_csv(path)
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "已导出", f"历史报告已导出至：\n{path}")
