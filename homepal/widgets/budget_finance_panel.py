from __future__ import annotations

from sqlalchemy import select
from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from homepal.models import BudgetEntry, Task
from homepal.services.task_service import TaskService


class BudgetFinancePanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Budget & Finance"))
        layout.addWidget(QLabel("Task costs are automatically synced here."))

        self.expenses_table = QTableWidget(0, 3)
        self.expenses_table.setHorizontalHeaderLabels(["Task", "Category", "Amount"])
        self.total_label = QLabel("Total tracked: $0.00")

        layout.addWidget(self.expenses_table)
        layout.addWidget(self.total_label)
        self.refresh()

    def refresh(self) -> None:
        rows = list(
            self.task_service.session.execute(
                select(BudgetEntry, Task.title).join(Task, Task.id == BudgetEntry.task_id).order_by(BudgetEntry.created_at.desc())
            )
        )
        self.expenses_table.setRowCount(0)
        total = 0.0
        for row_index, (entry, title) in enumerate(rows):
            self.expenses_table.insertRow(row_index)
            self.expenses_table.setItem(row_index, 0, QTableWidgetItem(title))
            self.expenses_table.setItem(row_index, 1, QTableWidgetItem(entry.category))
            self.expenses_table.setItem(row_index, 2, QTableWidgetItem(f"{entry.amount:.2f}"))
            total += float(entry.amount)
        self.total_label.setText(f"Total tracked: ${total:.2f}")
