from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BudgetFinancePanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Budget & Finance"))

        input_box = QGroupBox("Track an expense")
        form = QFormLayout(input_box)
        self.category_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        add_btn = QPushButton("Add expense")
        add_btn.clicked.connect(self.add_expense)

        form.addRow("Category", self.category_input)
        form.addRow("Amount", self.amount_input)
        form.addRow(add_btn)

        self.expenses_table = QTableWidget(0, 2)
        self.expenses_table.setHorizontalHeaderLabels(["Category", "Amount"])

        self.total_label = QLabel("Total tracked: $0.00")

        layout.addWidget(input_box)
        layout.addWidget(self.expenses_table)
        layout.addWidget(self.total_label)

    def add_expense(self) -> None:
        category = self.category_input.text().strip()
        amount_text = self.amount_input.text().strip()
        if not category or not amount_text:
            return

        try:
            amount = float(amount_text)
        except ValueError:
            return

        row = self.expenses_table.rowCount()
        self.expenses_table.insertRow(row)
        self.expenses_table.setItem(row, 0, QTableWidgetItem(category))
        self.expenses_table.setItem(row, 1, QTableWidgetItem(f"{amount:.2f}"))

        self.category_input.clear()
        self.amount_input.clear()
        self._update_total()

    def _update_total(self) -> None:
        total = 0.0
        for row in range(self.expenses_table.rowCount()):
            item = self.expenses_table.item(row, 1)
            if item is None:
                continue
            total += float(item.text())
        self.total_label.setText(f"Total tracked: ${total:.2f}")
