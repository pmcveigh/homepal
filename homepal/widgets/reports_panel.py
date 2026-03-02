from __future__ import annotations

from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from homepal.services.task_service import TaskService


class ReportsPanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reports"))

        self.report_output = QTextEdit()
        self.report_output.setReadOnly(True)

        generate_btn = QPushButton("Generate basic report")
        generate_btn.clicked.connect(self.generate_report)

        layout.addWidget(generate_btn)
        layout.addWidget(self.report_output)

    def generate_report(self) -> None:
        report = self.task_service.generate_report_summary()
        self.report_output.setPlainText(
            "\n".join(
                [
                    f"Total tasks: {report.total_tasks}",
                    f"Completed tasks: {report.completed_tasks}",
                    f"Open tasks: {report.open_tasks}",
                    f"Overdue tasks: {report.overdue_tasks}",
                    f"Urgent tasks: {report.urgent_tasks}",
                    f"Estimated cost total: {report.estimated_cost_total}",
                    f"Actual cost total: {report.actual_cost_total}",
                ]
            )
        )
