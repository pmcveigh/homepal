from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QVBoxLayout, QWidget

from homepal.services.task_service import TaskService


class DashboardPanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dashboard"))

        stats_box = QGroupBox("Current Snapshot")
        stats_form = QFormLayout(stats_box)

        self.open_label = QLabel("0")
        self.overdue_label = QLabel("0")
        self.p1_label = QLabel("0")
        self.week_label = QLabel("0")
        self.rooms_label = QLabel("0")
        self.assets_label = QLabel("0")

        stats_form.addRow("Open tasks", self.open_label)
        stats_form.addRow("Overdue tasks", self.overdue_label)
        stats_form.addRow("P1 tasks", self.p1_label)
        stats_form.addRow("Due this week", self.week_label)
        stats_form.addRow("Rooms", self.rooms_label)
        stats_form.addRow("Assets", self.assets_label)

        layout.addWidget(stats_box)
        layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        stats = self.task_service.get_dashboard_stats()
        self.open_label.setText(str(stats.open_tasks))
        self.overdue_label.setText(str(stats.overdue_tasks))
        self.p1_label.setText(str(stats.p1_tasks))
        self.week_label.setText(str(stats.due_this_week))
        self.rooms_label.setText(str(stats.total_rooms))
        self.assets_label.setText(str(stats.total_assets))
