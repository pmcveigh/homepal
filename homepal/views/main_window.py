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

from homepal.services.task_service import TaskService
from homepal.widgets.task_panel import TaskPanel


class MainWindow(QMainWindow):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service
        self.setWindowTitle("Homepal")
        self.resize(1200, 780)
        splitter = QSplitter(Qt.Horizontal)

        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        for section in ["Dashboard", "Tasks", "Rooms", "Assets", "Reports", "Settings"]:
            QTreeWidgetItem(self.nav, [section])

        self.stack = QStackedWidget()
        self.stack.addWidget(self._placeholder("Dashboard"))
        self.task_panel = TaskPanel(self.task_service)
        self.task_panel.data_changed.connect(self.update_status_bar)
        self.stack.addWidget(self.task_panel)
        for section in ["Rooms", "Assets", "Reports", "Settings"]:
            self.stack.addWidget(self._placeholder(section))

        self.nav.currentItemChanged.connect(self._on_nav)
        self.nav.setCurrentItem(self.nav.topLevelItem(0))

        splitter.addWidget(self.nav)
        splitter.addWidget(self.stack)
        splitter.setSizes([240, 960])
        self.setCentralWidget(splitter)

        status = QStatusBar()
        self.status_label = ""
        self.setStatusBar(status)
        self.update_status_bar()

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

    def update_status_bar(self) -> None:
        stats = self.task_service.get_dashboard_stats()
        self.statusBar().showMessage(
            f"Open: {stats.open_tasks} | Overdue: {stats.overdue_tasks} | P1: {stats.p1_tasks} | Due this week: {stats.due_this_week}"
        )
