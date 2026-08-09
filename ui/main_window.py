"""主窗口：左侧导航 + 右侧分页（录入 / 结果 / 建议 / 历史 / 周汇总）。"""

from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QMainWindow,
    QWidget,
    QStackedWidget,
)
from PyQt6.QtCore import Qt

import storage
from ui.input_panel import InputPanel
from ui.result_panel import ResultPanel
from ui.report_panel import ReportPanel
from ui.history_panel import HistoryPanel
from ui.weekly_panel import WeeklyPanel

STYLE = """
QWidget {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 14px;
    color: #2c3e50;
    background: #f5f7fa;
}
#pageTitle { font-size: 22px; font-weight: 700; color: #1f2d3d; }

QListWidget#sidebar {
    background: #2c3e50; color: #ecf0f1; border: none; padding: 8px 0;
}
QListWidget#sidebar::item { padding: 14px 18px; color: #ecf0f1; }
QListWidget#sidebar::item:selected { background: #1abc9c; color: #fff; }
QListWidget#sidebar::item:hover { background: #34495e; }

QGroupBox {
    background: #ffffff; border: 1px solid #e1e8ed; border-radius: 10px;
    padding: 16px; margin-top: 12px; font-weight: 600;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #34495e; }

QLineEdit, QDoubleSpinBox, QComboBox {
    background: #fff; border: 1px solid #d0d7de; border-radius: 8px;
    padding: 8px 10px;
}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #1abc9c; }

QPushButton {
    background: #ecf0f1; border: none; border-radius: 8px;
    padding: 10px 18px; color: #2c3e50;
}
QPushButton:hover { background: #dfe6e9; }
QPushButton#primaryBtn { background: #1abc9c; color: #fff; font-weight: 700; font-size: 15px; }
QPushButton#primaryBtn:hover { background: #16a085; }

QFrame#metricCard { background: #fff; border: 1px solid #e1e8ed; border-radius: 12px; }
#cardTitle { color: #7f8c8d; font-size: 13px; }
#cardValue { font-size: 26px; font-weight: 700; }
#cardSub { color: #95a5a6; font-size: 12px; }

#bmiHero {
    background: #fff; border: 1px solid #e1e8ed; border-radius: 12px;
    padding: 20px 24px;
}

QTableWidget {
    background: #fff; border: 1px solid #e1e8ed; border-radius: 10px;
    gridline-color: #eef2f5;
}
QHeaderView::section {
    background: #f0f3f5; padding: 8px; border: none; font-weight: 600;
}
QTableWidget::item { padding: 6px; }

QTextEdit {
    background: #fff; border: 1px solid #e1e8ed; border-radius: 10px; padding: 16px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("健康管理与数据分析中心")
        self.resize(1120, 740)
        self._build_ui()

        # 启动时自动周汇总（满足「每隔一星期」自动触发）
        storage.ensure_weekly_summaries()
        self.history_panel.refresh()
        self.weekly_panel.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(184)
        self.sidebar.addItems(["健康录入", "指标结果", "健康建议", "历史记录", "周汇总"])
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self._switch_page)
        root.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.input_panel = InputPanel()
        self.result_panel = ResultPanel()
        self.report_panel = ReportPanel()
        self.history_panel = HistoryPanel()
        self.weekly_panel = WeeklyPanel()
        for w in (
            self.input_panel,
            self.result_panel,
            self.report_panel,
            self.history_panel,
            self.weekly_panel,
        ):
            self.stack.addWidget(w)
        root.addWidget(self.stack, 1)

        self.input_panel.report_generated.connect(self.on_report_generated)
        self.history_panel.report_selected.connect(self.on_history_selected)
        self.history_panel.generate_requested.connect(
            lambda: self.sidebar.setCurrentRow(0)
        )

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)

    def on_report_generated(self, report_id: int):
        rep = storage.get_report(report_id)
        if not rep:
            return
        self.result_panel.show_report(rep)
        self.report_panel.show_report(rep)
        self.history_panel.refresh()
        storage.ensure_weekly_summaries(force=True)
        self.weekly_panel.refresh()
        self.sidebar.setCurrentRow(1)

    def on_history_selected(self, report_id: int):
        rep = storage.get_report(report_id)
        if not rep:
            return
        self.result_panel.show_report(rep)
        self.report_panel.show_report(rep)
        self.sidebar.setCurrentRow(1)
