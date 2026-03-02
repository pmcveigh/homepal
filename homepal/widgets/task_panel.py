from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
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

        self.urgent_input = QCheckBox("Urgent")
        self.follow_up_input = QCheckBox("Needs follow-up")
        self.estimated_effort_input = QLineEdit()
        self.estimated_effort_input.setPlaceholderText("e.g. 1.5")
        self.labels_input = QLineEdit()
        self.labels_input.setPlaceholderText("comma-separated labels")

        create_button = QPushButton("Add Task")
        create_button.clicked.connect(self._create_task)

        form.addRow("Title", self.title_input)
        form.addRow("Description", self.description_input)
        form.addRow("Priority", self.priority_input)
        form.addRow("Due date", self.due_date_input)
        form.addRow("Urgency", self.urgent_input)
        form.addRow("Follow-up", self.follow_up_input)
        form.addRow("Effort (hours)", self.estimated_effort_input)
        form.addRow("Labels", self.labels_input)
        form.addRow(create_button)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Title", "Priority", "Status", "Due", "Flags", "Labels", "Actions"])
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

            flags = []
            if task.is_urgent:
                flags.append("Urgent")
            if task.requires_follow_up:
                flags.append("Follow-up")
            if task.estimated_effort_hours is not None:
                flags.append(f"{task.estimated_effort_hours}h")
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(flags) if flags else "-"))
            self.table.setItem(row, 5, QTableWidgetItem(task.labels or "-"))

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
            self.table.setCellWidget(row, 6, action_cell)

        self.table.resizeColumnsToContents()

    def _create_task(self) -> None:
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation", "Title is required.")
            return

        effort_text = self.estimated_effort_input.text().strip()
        effort = None
        if effort_text:
            try:
                effort = Decimal(effort_text)
            except InvalidOperation:
                QMessageBox.warning(self, "Validation", "Effort must be a valid number.")
                return

        due = self.due_date_input.date().toPython()
        self.task_service.create_task(
            title=title,
            description=self.description_input.toPlainText(),
            priority=self.priority_input.currentData(Qt.UserRole),
            due_date=due,
            is_urgent=self.urgent_input.isChecked(),
            requires_follow_up=self.follow_up_input.isChecked(),
            estimated_effort_hours=effort,
            labels=self.labels_input.text(),
        )
        self.task_service.session.commit()

        self.title_input.clear()
        self.description_input.clear()
        self.urgent_input.setChecked(False)
        self.follow_up_input.setChecked(False)
        self.estimated_effort_input.clear()
        self.labels_input.clear()
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
