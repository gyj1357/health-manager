"""健康数据录入面板。"""

from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal, Qt

from calc import ActivityLevel, Gender, compute_all, ACTIVITY_LABELS_ZH
import report_gen
import storage


class InputPanel(QWidget):
    report_generated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("健康数据录入")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("选填，便于区分不同人")

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])

        self.age_spin = QDoubleSpinBox()
        self.age_spin.setRange(1, 120)
        self.age_spin.setValue(30)
        self.age_spin.setSuffix(" 岁")

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(50, 250)
        self.height_spin.setValue(170)
        self.height_spin.setSuffix(" cm")

        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(10, 300)
        self.weight_spin.setValue(65)
        self.weight_spin.setSuffix(" kg")

        self.activity_combo = QComboBox()
        for lvl in ActivityLevel:
            self.activity_combo.addItem(ACTIVITY_LABELS_ZH[lvl], lvl)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(12)
        form.addRow("姓名", self.name_edit)
        form.addRow("性别", self.gender_combo)
        form.addRow("年龄", self.age_spin)
        form.addRow("身高", self.height_spin)
        form.addRow("体重", self.weight_spin)
        form.addRow("活动水平", self.activity_combo)

        card = QGroupBox("基本信息")
        card.setLayout(form)
        layout.addWidget(card)

        self.gen_btn = QPushButton("生成健康报告")
        self.gen_btn.setObjectName("primaryBtn")
        self.gen_btn.clicked.connect(self._generate)
        layout.addWidget(self.gen_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def _generate(self):
        try:
            gender = (
                Gender.MALE if self.gender_combo.currentText() == "男" else Gender.FEMALE
            )
            age = self.age_spin.value()
            height = self.height_spin.value()
            weight = self.weight_spin.value()
            activity = self.activity_combo.currentData()

            result = compute_all(weight, height, age, gender, activity)
            advice = report_gen.generate_advice(result, gender, age)
            rid = storage.save_report(
                result,
                name=self.name_edit.text().strip() or None,
                gender=gender,
                age=age,
                height=height,
                weight=weight,
                activity=activity,
                advice=advice,
            )
            self.report_generated.emit(rid)
        except Exception as e:  # noqa: BLE001 - 用户输入异常需友好提示
            QMessageBox.warning(self, "无法生成报告", str(e))
