from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from homepal.services.task_service import TaskService


class RoomsAssetsPanel(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.on_data_changed = on_data_changed

        layout = QHBoxLayout(self)

        room_box = QGroupBox("Rooms")
        room_layout = QVBoxLayout(room_box)
        room_form = QFormLayout()
        self.room_name = QLineEdit()
        self.room_desc = QLineEdit()
        self.room_floor = QLineEdit()
        room_form.addRow("Name", self.room_name)
        room_form.addRow("Description", self.room_desc)
        room_form.addRow("Floor", self.room_floor)
        room_layout.addLayout(room_form)
        add_room_btn = QPushButton("Add Room")
        add_room_btn.clicked.connect(self._add_room)
        room_layout.addWidget(add_room_btn)
        self.rooms_list = QListWidget()
        room_layout.addWidget(QLabel("Existing rooms"))
        room_layout.addWidget(self.rooms_list)

        asset_box = QGroupBox("Assets")
        asset_layout = QVBoxLayout(asset_box)
        asset_form = QFormLayout()
        self.asset_room_name = QLineEdit()
        self.asset_name = QLineEdit()
        self.asset_category = QLineEdit()
        self.asset_notes = QLineEdit()
        asset_form.addRow("Room name", self.asset_room_name)
        asset_form.addRow("Name", self.asset_name)
        asset_form.addRow("Category", self.asset_category)
        asset_form.addRow("Notes", self.asset_notes)
        asset_layout.addLayout(asset_form)
        add_asset_btn = QPushButton("Add Asset")
        add_asset_btn.clicked.connect(self._add_asset)
        asset_layout.addWidget(add_asset_btn)
        self.assets_list = QListWidget()
        asset_layout.addWidget(QLabel("Existing assets"))
        asset_layout.addWidget(self.assets_list)

        layout.addWidget(room_box)
        layout.addWidget(asset_box)

        self.refresh()

    def refresh(self) -> None:
        rooms = self.task_service.list_rooms()
        assets = self.task_service.list_assets()

        self.rooms_list.clear()
        for room in rooms:
            detail = f" ({room.floor_level})" if room.floor_level else ""
            self.rooms_list.addItem(f"{room.name}{detail}")

        self.assets_list.clear()
        room_lookup = {room.id: room.name for room in rooms}
        for asset in assets:
            self.assets_list.addItem(f"{asset.name} [{asset.category}] - {room_lookup.get(asset.room_id, 'Unknown room')}")

    def _add_room(self) -> None:
        name = self.room_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Room name is required.")
            return
        self.task_service.create_room(name=name, description=self.room_desc.text(), floor_level=self.room_floor.text())
        self.task_service.session.commit()
        self.room_name.clear()
        self.room_desc.clear()
        self.room_floor.clear()
        self.refresh()
        self.on_data_changed()

    def _add_asset(self) -> None:
        room_name = self.asset_room_name.text().strip()
        if not room_name:
            QMessageBox.warning(self, "Validation", "Room name is required to attach an asset.")
            return

        rooms = self.task_service.list_rooms()
        room = next((r for r in rooms if r.name.lower() == room_name.lower()), None)
        if room is None:
            QMessageBox.warning(self, "Validation", f"Room '{room_name}' does not exist.")
            return

        name = self.asset_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Asset name is required.")
            return

        self.task_service.create_asset(
            room_id=room.id,
            name=name,
            category=self.asset_category.text(),
            notes=self.asset_notes.text(),
        )
        self.task_service.session.commit()
        self.asset_room_name.clear()
        self.asset_name.clear()
        self.asset_category.clear()
        self.asset_notes.clear()
        self.refresh()
        self.on_data_changed()
