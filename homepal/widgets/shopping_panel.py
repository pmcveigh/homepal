from __future__ import annotations

from sqlalchemy import select
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from homepal.models import ShoppingListItem
from homepal.services.task_service import TaskService


class ShoppingPanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Shopping"))
        layout.addWidget(QLabel("Generated from task required materials."))

        self.items_layout = QVBoxLayout()
        layout.addLayout(self.items_layout)

        clear_btn = QPushButton("Clear completed")
        clear_btn.clicked.connect(self.clear_completed)
        layout.addWidget(clear_btn)
        layout.addStretch()

        self.refresh()

    def refresh(self) -> None:
        for i in reversed(range(self.items_layout.count())):
            widget = self.items_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        items = list(self.task_service.session.scalars(select(ShoppingListItem).order_by(ShoppingListItem.id.asc())))
        for entry in items:
            checkbox = QCheckBox(entry.label)
            checkbox.setChecked(entry.is_purchased)
            checkbox.stateChanged.connect(lambda state, item_id=entry.id: self._toggle(item_id, state != 0))
            self.items_layout.addWidget(checkbox)

    def _toggle(self, item_id: str, purchased: bool) -> None:
        item = self.task_service.session.get(ShoppingListItem, item_id)
        if item is None:
            return
        item.is_purchased = purchased
        self.task_service.session.commit()

    def clear_completed(self) -> None:
        completed = list(self.task_service.session.scalars(select(ShoppingListItem).where(ShoppingListItem.is_purchased.is_(True))))
        for item in completed:
            self.task_service.session.delete(item)
        self.task_service.session.commit()
        self.refresh()
