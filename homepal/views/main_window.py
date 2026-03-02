from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Homepal")
        self.resize(1200, 780)
        splitter = QSplitter(Qt.Horizontal)

        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        for section in ["Dashboard", "Tasks", "Rooms", "Assets", "Reports", "Settings"]:
            QTreeWidgetItem(self.nav, [section])

        self.stack = QStackedWidget()
        for section in ["Dashboard", "Tasks", "Rooms", "Assets", "Reports", "Settings"]:
            self.stack.addWidget(self._placeholder(section))

        self.nav.currentItemChanged.connect(self._on_nav)
        self.nav.setCurrentItem(self.nav.topLevelItem(0))

        splitter.addWidget(self.nav)
        splitter.addWidget(self.stack)
        splitter.setSizes([240, 960])
        self.setCentralWidget(splitter)

        status = QStatusBar()
        status.showMessage("Open: 0 | Overdue: 0 | P1: 0")
        self.setStatusBar(status)

    def _placeholder(self, title: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(f"{title} view (MVP scaffold)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def _on_nav(self, current, _previous):
        if current is None:
            return
        self.stack.setCurrentIndex(self.nav.indexOfTopLevelItem(current))
