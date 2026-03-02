from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget

from homepal.services.task_service import TaskService


class CalendarPanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service
        self.current = date.today().replace(day=1)

        layout = QVBoxLayout(self)
        self.header = QLabel()
        self.tasks_list = QListWidget()

        prev_btn = QPushButton("Previous month")
        next_btn = QPushButton("Next month")
        prev_btn.clicked.connect(self._previous_month)
        next_btn.clicked.connect(self._next_month)

        layout.addWidget(QLabel("Calendar View"))
        layout.addWidget(self.header)
        layout.addWidget(prev_btn)
        layout.addWidget(next_btn)
        layout.addWidget(self.tasks_list)

        self.refresh()

    def _previous_month(self) -> None:
        if self.current.month == 1:
            self.current = self.current.replace(year=self.current.year - 1, month=12)
        else:
            self.current = self.current.replace(month=self.current.month - 1)
        self.refresh()

    def _next_month(self) -> None:
        if self.current.month == 12:
            self.current = self.current.replace(year=self.current.year + 1, month=1)
        else:
            self.current = self.current.replace(month=self.current.month + 1)
        self.refresh()

    def refresh(self) -> None:
        self.header.setText(self.current.strftime("%B %Y"))
        self.tasks_list.clear()
        tasks = self.task_service.list_calendar_tasks(month=self.current.month, year=self.current.year)
        for task in tasks:
            self.tasks_list.addItem(f"{task.due_date.isoformat()} - {task.title} ({task.status.value})")
        if not tasks:
            self.tasks_list.addItem("No tasks scheduled for this month.")
