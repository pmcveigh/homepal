from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from homepal.models import HouseholdMember
from homepal.services.task_service import TaskService


class HouseholdMembersPanel(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.on_data_changed = on_data_changed

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Household Members"))

        input_row = QHBoxLayout()
        self.member_input = QLineEdit(); self.member_input.setPlaceholderText("Name")
        self.email_input = QLineEdit(); self.email_input.setPlaceholderText("Email (optional)")
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove selected")
        add_btn.clicked.connect(self.add_member)
        remove_btn.clicked.connect(self.remove_selected)

        for widget in [self.member_input, self.email_input, add_btn, remove_btn]:
            input_row.addWidget(widget)

        self.members_list = QListWidget()

        layout.addLayout(input_row)
        layout.addWidget(self.members_list)
        self.refresh()

    def refresh(self) -> None:
        self.members_list.clear()
        for member in self.task_service.list_household_members():
            item = QListWidgetItem(f"{member.name} ({member.email or 'no email'})")
            item.setData(Qt.UserRole, member.id)
            self.members_list.addItem(item)

    def add_member(self) -> None:
        name = self.member_input.text().strip()
        if not name:
            return
        try:
            self.task_service.create_household_member(name=name, email=self.email_input.text())
            self.task_service.session.commit()
            self.member_input.clear(); self.email_input.clear()
            self.refresh()
            self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Add failed", str(exc))

    def remove_selected(self) -> None:
        item = self.members_list.currentItem()
        if item is None:
            return
        member_id = item.data(Qt.UserRole)
        member = self.task_service.session.get(HouseholdMember, member_id)
        if member is None:
            return
        try:
            self.task_service.session.delete(member)
            self.task_service.session.commit()
            self.refresh()
            self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Delete failed", str(exc))
