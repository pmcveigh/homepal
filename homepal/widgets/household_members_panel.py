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


class HouseholdMembersPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Household Members"))

        input_row = QHBoxLayout()
        self.member_input = QLineEdit()
        self.member_input.setPlaceholderText("Add a household member")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_member)
        remove_btn = QPushButton("Remove selected")
        remove_btn.clicked.connect(self.remove_selected)

        input_row.addWidget(self.member_input)
        input_row.addWidget(add_btn)
        input_row.addWidget(remove_btn)

        self.members_list = QListWidget()

        layout.addLayout(input_row)
        layout.addWidget(self.members_list)

    def add_member(self) -> None:
        name = self.member_input.text().strip()
        if not name:
            return
        self.members_list.addItem(name)
        self.member_input.clear()

    def remove_selected(self) -> None:
        for item in self.members_list.selectedItems():
            row = self.members_list.row(item)
            self.members_list.takeItem(row)
