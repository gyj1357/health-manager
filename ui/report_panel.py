"""个性化健康建议报告面板（Markdown 富文本渲染）。"""

from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QLabel, QWidget


class ReportPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel("个性化健康建议")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)
        self._empty()

    def _empty(self):
        self.text.setPlainText(
            "暂无报告。请先在「健康录入」生成报告，或点击左侧「历史记录」查看往期报告。"
        )

    def show_report(self, rep: dict):
        self.text.setMarkdown(rep["advice"])
