from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from homepal.models import Priority, TaskStatus
from homepal.services.task_service import TaskService


class TaskPanel(QWidget):
    data_changed = Signal()

    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Tasks"))

        form_box = QGroupBox("Create Task")
        form = QFormLayout(form_box)

        self.title_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setFixedHeight(80)

        self.priority_input = QComboBox()
        for priority in Priority:
            self.priority_input.addItem(priority.value, priority)

        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(date.today())

        create_button = QPushButton("Add Task")
        create_button.clicked.connect(self._create_task)

        form.addRow("Title", self.title_input)
        form.addRow("Description", self.description_input)
        form.addRow("Priority", self.priority_input)
        form.addRow("Due date", self.due_date_input)
        form.addRow(create_button)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Title", "Priority", "Status", "Due", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(form_box)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        tasks = self.task_service.list_tasks()
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            self.table.setItem(row, 0, QTableWidgetItem(task.title))
            self.table.setItem(row, 1, QTableWidgetItem(task.priority.value))
            self.table.setItem(row, 2, QTableWidgetItem(task.status.value))
            self.table.setItem(row, 3, QTableWidgetItem(task.due_date.isoformat() if task.due_date else "-"))

            action_cell = QWidget()
            action_layout = QHBoxLayout(action_cell)
            action_layout.setContentsMargins(0, 0, 0, 0)

            if task.status in {TaskStatus.OPEN, TaskStatus.BLOCKED}:
                button = QPushButton("Start")
                button.clicked.connect(lambda _checked=False, t=task: self._transition_task(t, TaskStatus.IN_PROGRESS))
            elif task.status == TaskStatus.IN_PROGRESS:
                button = QPushButton("Complete")
                button.clicked.connect(lambda _checked=False, t=task: self._transition_task(t, TaskStatus.COMPLETED))
            else:
                button = QPushButton("-")
                button.setEnabled(False)

            action_layout.addWidget(button)
            action_layout.addStretch()
            self.table.setCellWidget(row, 4, action_cell)

        self.table.resizeColumnsToContents()

    def _create_task(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title is required.")
            return

        due = self.due_date_input.date().toPython()
        self.task_service.create_task(
            title=title,
            description=self.description_input.toPlainText(),
            priority=self.priority_input.currentData(Qt.UserRole),
            due_date=due,
        )
        self.task_service.session.commit()

        self.title_input.clear()
        self.description_input.clear()
        self.refresh()
        self.data_changed.emit()

    def _transition_task(self, task, new_status: TaskStatus) -> None:
        try:
            self.task_service.transition_status(task, new_status)
            self.task_service.session.commit()
        except ValueError as exc:
            QMessageBox.warning(self, "Transition error", str(exc))
            self.task_service.session.rollback()
            return

        self.refresh()
        self.data_changed.emit()
