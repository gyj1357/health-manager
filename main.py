"""程序入口。"""

import sys

from PyQt6.QtWidgets import QApplication

import storage
from ui.main_window import MainWindow, STYLE


def main():
    storage.init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    app.setApplicationName("健康管理与数据分析中心")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
