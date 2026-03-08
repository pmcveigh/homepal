from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ShoppingPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Shopping"))

        input_row = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Add shopping item")
        add_btn = QPushButton("Add item")
        add_btn.clicked.connect(self.add_item)

        input_row.addWidget(self.item_input)
        input_row.addWidget(add_btn)

        self.items_layout = QVBoxLayout()
        self.items_layout.setAlignment(Qt.AlignTop)

        clear_btn = QPushButton("Clear completed")
        clear_btn.clicked.connect(self.clear_completed)

        layout.addLayout(input_row)
        layout.addLayout(self.items_layout)
        layout.addWidget(clear_btn)
        layout.addStretch()

    def add_item(self) -> None:
        text = self.item_input.text().strip()
        if not text:
            return
        checkbox = QCheckBox(text)
        self.items_layout.addWidget(checkbox)
        self.item_input.clear()

    def clear_completed(self) -> None:
        for index in reversed(range(self.items_layout.count())):
            widget = self.items_layout.itemAt(index).widget()
            if isinstance(widget, QCheckBox) and widget.isChecked():
                widget.setParent(None)
