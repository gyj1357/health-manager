"""指标结果面板：BMI 主视觉 + 指标卡片 + BMI 趋势折线图。"""

from datetime import datetime

from PyQt6.QtCharts import (
    QChart,
    QChartView,
    QDateTimeAxis,
    QLineSeries,
    QValueAxis,
)
from PyQt6.QtCore import Qt, QDateTime, QPointF
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from calc import classify_bmi
import storage


class ResultPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self._empty_state()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("健康指标结果")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.bmi_hero = QLabel()
        self.bmi_hero.setObjectName("bmiHero")
        layout.addWidget(self.bmi_hero)

        self.cards = QGridLayout()
        self.cards.setSpacing(14)
        layout.addLayout(self.cards)

        self.chart_view = QChartView()
        self.chart_view.setMinimumHeight(230)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self.chart_view)
        layout.addStretch()

    def _empty_state(self):
        self.bmi_hero.setText(
            '<div style="color:#7f8c8d;">暂无数据</div>'
            '<div style="margin-top:6px;">请先在「健康录入」中生成报告</div>'
        )
        self._clear_cards()
        self.chart_view.setChart(QChart())

    def _clear_cards(self):
        while self.cards.count():
            item = self.cards.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _card(self, title: str, value: str, sub: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("metricCard")
        v = QVBoxLayout(card)
        v.setContentsMargins(14, 12, 14, 12)
        t = QLabel(title)
        t.setObjectName("cardTitle")
        val = QLabel(value)
        val.setObjectName("cardValue")
        val.setStyleSheet(f"color:{color};")
        v.addWidget(t)
        v.addWidget(val)
        if sub:
            s = QLabel(sub)
            s.setObjectName("cardSub")
            v.addWidget(s)
        return card

    def show_report(self, rep: dict):
        self._clear_cards()
        _, label, color = classify_bmi(rep["bmi"])
        self.bmi_hero.setText(
            '<div style="font-size:15px;color:#7f8c8d;">身体质量指数 BMI</div>'
            f'<div style="margin-top:4px;">'
            f'<font size=6 color="{color}"><b>{rep["bmi"]:.1f}</b></font>'
            f'&nbsp; <span style="background:{color};color:#fff;'
            f'padding:3px 12px;border-radius:12px;font-size:13px;">{label}</span></div>'
        )

        bf_label = rep["body_fat_label"]
        bf_color = {
            "健康": "#27ae60",
            "偏低": "#3498db",
            "偏高": "#e67e22",
            "肥胖": "#e74c3c",
        }.get(bf_label, "#2c3e50")

        self.cards.addWidget(
            self._card("基础代谢率 BMR", f'{rep["bmr"]:.0f}', "kcal/天", "#2c3e50"), 0, 0
        )
        self.cards.addWidget(
            self._card("每日总消耗 TDEE", f'{rep["tdee"]:.0f}', "kcal/天", "#2c3e50"),
            0, 1,
        )
        self.cards.addWidget(
            self._card("体脂率估算", f'{rep["body_fat"]:.1f}%', bf_label, bf_color), 0, 2
        )
        self.cards.addWidget(
            self._card(
                "健康体重区间",
                f'{rep["healthy_low"]:.1f}~{rep["healthy_high"]:.1f}',
                "kg",
                "#16a085",
            ),
            0, 3,
        )
        self._update_chart()

    def _update_chart(self):
        reports = storage.list_reports() or []
        reports.sort(key=lambda r: r["ts"])

        chart = QChart()
        chart.setTitle("BMI 变化趋势")
        chart.legend().hide()

        if reports:
            series = QLineSeries()
            series.setName("BMI")
            for r in reports:
                py_dt = datetime.fromisoformat(r["ts"])
                qdt = QDateTime(
                    py_dt.year, py_dt.month, py_dt.day,
                    py_dt.hour, py_dt.minute, py_dt.second,
                )
                series.append(QPointF(qdt.toMSecsSinceEpoch(), r["bmi"]))
            chart.addSeries(series)

            axis_x = QDateTimeAxis()
            axis_x.setFormat("MM-dd")
            axis_x.setTitleText("时间")
            axis_y = QValueAxis()
            axis_y.setTitleText("BMI")
            axis_y.setRange(15, 35)
            chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        self.chart_view.setChart(chart)
