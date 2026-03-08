from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MealPlanningPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Meal Planning"))

        entry_row = QHBoxLayout()
        self.day_input = QLineEdit()
        self.day_input.setPlaceholderText("Day")
        self.meal_input = QLineEdit()
        self.meal_input.setPlaceholderText("Meal")
        add_btn = QPushButton("Plan meal")
        add_btn.clicked.connect(self.add_plan)

        entry_row.addWidget(self.day_input)
        entry_row.addWidget(self.meal_input)
        entry_row.addWidget(add_btn)

        self.plan_list = QListWidget()

        layout.addLayout(entry_row)
        layout.addWidget(self.plan_list)

    def add_plan(self) -> None:
        day = self.day_input.text().strip()
        meal = self.meal_input.text().strip()
        if not day or not meal:
            return
        self.plan_list.addItem(f"{day}: {meal}")
        self.day_input.clear()
        self.meal_input.clear()
