from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from homepal.models import LinkRole
from homepal.services.asset_service import AssetSaveDTO, AssetService
from homepal.services.room_service import RoomSaveDTO, RoomService
from homepal.services.task_service import AssetListRow, RoomListRow, TaskService
from homepal.widgets.metadata_form import MetadataFormWidget


ROOM_TYPES = ["any", "kitchen", "bathroom", "bedroom", "living_room", "dining_room", "office", "utility", "laundry", "garage", "hall", "outdoor"]


def _normalize_room_type(raw_value: str | None) -> str:
    value = (raw_value or "").strip().lower()
    return value if value in ROOM_TYPES else "any"


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, headers: list[str]):
        super().__init__()
        self.headers = headers
        self.rows: list[tuple] = []

    def set_rows(self, rows: list[tuple]):
        self.beginResetModel(); self.rows = rows; self.endResetModel()

    def rowCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.rows)
    def columnCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.headers)
    def headerData(self, sec, ori, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and ori == Qt.Horizontal: return self.headers[sec]
        return None
    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid() or role != Qt.DisplayRole: return None
        return str(self.rows[idx.row()][idx.column()])


class AddRoomDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Room")
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.room_type = QComboBox(); self.room_type.addItems(ROOM_TYPES)
        self.floor = QLineEdit()
        self.notes = QTextEdit()
        layout.addRow("Name", self.name)
        layout.addRow("Type", self.room_type)
        layout.addRow("Floor", self.floor)
        layout.addRow("Notes", self.notes)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class AddAssetDialog(QDialog):
    def __init__(self, rooms: list[tuple[str, str]], categories: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add Asset")
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.category = QComboBox(); self.category.addItems(categories or ["General"])
        self.primary_room = QComboBox()
        for room_id, room_name in rooms:
            self.primary_room.addItem(room_name, room_id)
        self.notes = QTextEdit()
        layout.addRow("Name", self.name)
        layout.addRow("Category", self.category)
        layout.addRow("Primary room", self.primary_room)
        layout.addRow("Notes", self.notes)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class RoomsTab(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.room_service = RoomService(task_service)
        self.on_data_changed = on_data_changed
        self.current_room_id: str | None = None

        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.add_room_btn = QPushButton("Add Room")
        self.delete_room_btn = QPushButton("Delete Room")
        self.delete_room_btn.setEnabled(False)
        self.room_search = QLineEdit(); self.room_search.setPlaceholderText("Search rooms")
        self.room_type = QComboBox(); self.room_type.addItems(ROOM_TYPES)
        toolbar.addWidget(self.add_room_btn)
        toolbar.addWidget(self.delete_room_btn)
        toolbar.addWidget(self.room_search)
        toolbar.addWidget(self.room_type)
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter)

        top = QWidget(); top_l = QVBoxLayout(top)
        self.rooms_model = SimpleTableModel(["Name", "Type", "Floor", "Asset count", "Open tasks", "Overdue tasks"])
        self.rooms_table = QTableView(); self.rooms_table.setModel(self.rooms_model)
        top_l.addWidget(self.rooms_table)

        bottom = QWidget(); bottom_l = QVBoxLayout(bottom)
        self.room_tab = QTabWidget(); bottom_l.addWidget(self.room_tab)
        self._build_room_tabs()

        splitter.addWidget(top); splitter.addWidget(bottom); splitter.setSizes([360, 380])

        self.add_room_btn.clicked.connect(self._add_room)
        self.delete_room_btn.clicked.connect(self._delete_room)
        self.room_search.textChanged.connect(self.refresh)
        self.room_type.currentIndexChanged.connect(self.refresh)
        self.rooms_table.selectionModel().selectionChanged.connect(self._room_selected)

        self.refresh()

    def _build_room_tabs(self):
        basics = QWidget(); form = QFormLayout(basics)
        self.room_name = QLineEdit(); self.room_type_edit = QComboBox(); self.room_type_edit.addItems(ROOM_TYPES)
        self.room_floor = QLineEdit(); self.room_notes = QTextEdit(); self.room_save_btn = QPushButton("Save room")
        for lbl, w in [("Name", self.room_name), ("Type", self.room_type_edit), ("Floor", self.room_floor), ("Notes", self.room_notes), ("", self.room_save_btn)]: form.addRow(lbl, w)
        self.room_tab.addTab(basics, "Basics")

        char_tab = QWidget(); char_l = QVBoxLayout(char_tab); self.room_metadata = MetadataFormWidget(task_service=self.task_service, owner_type="room")
        char_l.addWidget(self.room_metadata); self.room_tab.addTab(char_tab, "Characteristics")

        tasks = QWidget(); tl = QVBoxLayout(tasks); self.room_direct_tasks = QListWidget(); self.room_derived_tasks = QListWidget()
        tl.addWidget(QLabel("Tasks assigned to this room")); tl.addWidget(self.room_direct_tasks)
        tl.addWidget(QLabel("Tasks where ABOUT asset in this room is involved")); tl.addWidget(self.room_derived_tasks)
        row = QHBoxLayout(); self.room_new_task = QPushButton("New task"); self.room_link_task = QPushButton("Link existing task"); self.room_unlink_task = QPushButton("Unlink")
        row.addWidget(self.room_new_task); row.addWidget(self.room_link_task); row.addWidget(self.room_unlink_task); tl.addLayout(row)
        self.room_tab.addTab(tasks, "Tasks")
        self.room_save_btn.clicked.connect(self._save_room)

    def refresh(self) -> None:
        rows = self.room_service.list_rooms_overview(search=self.room_search.text(), room_type=self.room_type.currentText())
        self._room_rows: list[RoomListRow] = rows
        self.rooms_model.set_rows([(r.name, r.room_type, r.floor_level or "-", r.asset_count, r.open_tasks_count, r.overdue_tasks_count) for r in rows])
        self.rooms_table.resizeColumnsToContents()
        if self.current_room_id and not any(room.id == self.current_room_id for room in rows):
            self.current_room_id = None
            self.delete_room_btn.setEnabled(False)

    def _select_room(self, room_id: str | None) -> None:
        if not room_id:
            return
        for index, room in enumerate(getattr(self, "_room_rows", [])):
            if room.id == room_id:
                self.rooms_table.selectRow(index)
                self._room_selected()
                return

    def _room_selected(self):
        selected = self.rooms_table.selectionModel().selectedRows()
        if not selected:
            return
        room = self._room_rows[selected[0].row()]
        self.current_room_id = room.id
        self.delete_room_btn.setEnabled(True)
        full = next((r for r in self.task_service.list_rooms() if r.id == room.id), None)
        if full:
            room_type = _normalize_room_type(full.description)
            self.room_name.setText(full.name); self.room_type_edit.setCurrentText(room_type); self.room_floor.setText(full.floor_level or ""); self.room_notes.setText(full.notes or "")
            self.room_metadata.rebuild(room_type=room_type, owner_id=room.id)
        direct, derived = self.task_service.list_task_titles_for_room(room.id)
        self.room_direct_tasks.clear(); self.room_direct_tasks.addItems([t.title for t in direct])
        self.room_derived_tasks.clear(); self.room_derived_tasks.addItems([t.title for t in derived])

    def _add_room(self):
        dialog = AddRoomDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not dialog.name.text().strip():
            QMessageBox.warning(self, "Validation", "Room name required")
            return
        try:
            room = self.room_service.save_room(
                RoomSaveDTO(
                    name=dialog.name.text(),
                    room_type=dialog.room_type.currentText(),
                    floor_level=dialog.floor.text(),
                    notes=dialog.notes.toPlainText(),
                )
            )
            self.task_service.session.commit()
            self.refresh(); self._select_room(room.id); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))

    def _save_room(self):
        if not self.room_name.text().strip():
            QMessageBox.warning(self, "Validation", "Room name required")
            return
        try:
            room = self.room_service.save_room(RoomSaveDTO(id=self.current_room_id, name=self.room_name.text(), room_type=self.room_type_edit.currentText(), floor_level=self.room_floor.text(), notes=self.room_notes.toPlainText()))
            self.room_metadata.persist_values(room.id)
            self.task_service.session.commit()
            self.refresh(); self._select_room(room.id); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))

    def _delete_room(self):
        if not self.current_room_id:
            QMessageBox.information(self, "Delete room", "Select a room to delete")
            return
        selected = self.rooms_table.selectionModel().selectedRows()
        room_name = self._room_rows[selected[0].row()].name if selected else "this room"
        answer = QMessageBox.question(
            self,
            "Delete room",
            f"Delete room '{room_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.room_service.delete_room(self.current_room_id)
            self.task_service.session.commit()
            self.current_room_id = None
            self.delete_room_btn.setEnabled(False)
            self.refresh(); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Delete failed", str(exc))


class AssetsTab(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.asset_service = AssetService(task_service)
        self.on_data_changed = on_data_changed
        self.current_asset_id: str | None = None

        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.add_asset_btn = QPushButton("Add Asset")
        self.delete_asset_btn = QPushButton("Delete Asset")
        self.delete_asset_btn.setEnabled(False)
        self.asset_search = QLineEdit(); self.asset_search.setPlaceholderText("Search assets")
        self.asset_category = QComboBox(); self.asset_category.addItem("any")
        self.room_filter = QComboBox(); self.room_filter.addItem("all rooms", None)
        self.warranty_soon = QCheckBox("Warranty soon")
        self.portable_only = QCheckBox("Portable only")
        for w in [self.add_asset_btn, self.delete_asset_btn, self.asset_search, self.asset_category, self.room_filter, self.warranty_soon, self.portable_only]:
            toolbar.addWidget(w)
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Vertical)
        root.addWidget(splitter)

        top = QWidget(); top_l = QVBoxLayout(top)
        self.assets_model = SimpleTableModel(["Name", "Category", "Fixed", "Warranty", "Value", "Primary"])
        self.assets_table = QTableView(); self.assets_table.setModel(self.assets_model)
        top_l.addWidget(self.assets_table)

        bottom = QWidget(); bottom_l = QVBoxLayout(bottom)
        self.asset_tab = QTabWidget(); bottom_l.addWidget(self.asset_tab)
        self._build_asset_tabs()

        splitter.addWidget(top); splitter.addWidget(bottom); splitter.setSizes([360, 380])

        self.add_asset_btn.clicked.connect(self._add_asset)
        self.delete_asset_btn.clicked.connect(self._delete_asset)
        self.asset_search.textChanged.connect(self.refresh)
        self.asset_category.currentIndexChanged.connect(self.refresh)
        self.room_filter.currentIndexChanged.connect(self.refresh)
        self.warranty_soon.stateChanged.connect(self.refresh)
        self.portable_only.stateChanged.connect(self.refresh)
        self.assets_table.selectionModel().selectionChanged.connect(self._asset_selected)

        self.refresh()

    def _build_asset_tabs(self):
        basics = QWidget(); form = QFormLayout(basics)
        self.asset_name = QLineEdit(); self.asset_category_edit = QComboBox(); self.asset_fixed = QCheckBox("Fixed")
        self.asset_vendor = QLineEdit(); self.asset_notes = QTextEdit(); self.asset_save_btn = QPushButton("Save asset")
        for lbl, w in [("Name", self.asset_name), ("Category", self.asset_category_edit), ("", self.asset_fixed), ("Vendor", self.asset_vendor), ("Notes", self.asset_notes), ("", self.asset_save_btn)]: form.addRow(lbl, w)
        self.asset_tab.addTab(basics, "Basics")

        rooms_tab = QWidget(); rf = QFormLayout(rooms_tab); self.primary_room = QComboBox(); self.used_rooms = QListWidget(); self.location_notes = QLineEdit(); rf.addRow("Primary room", self.primary_room); rf.addRow("Also used in", self.used_rooms); rf.addRow("Location notes", self.location_notes)
        self.asset_tab.addTab(rooms_tab, "Rooms")

        chars = QWidget(); cl = QVBoxLayout(chars); self.asset_metadata = MetadataFormWidget(task_service=self.task_service, owner_type="asset")
        cl.addWidget(self.asset_metadata); self.asset_tab.addTab(chars, "Characteristics")

        docs = QWidget(); dl = QVBoxLayout(docs); d = QLabel("Attachments with receipt shortcut (coming soon)"); d.setEnabled(False); dl.addWidget(d); self.asset_tab.addTab(docs, "Documents")

        ttab = QWidget(); tl = QVBoxLayout(ttab); self.about_tasks = QListWidget(); self.uses_tasks = QListWidget(); self.requires_tasks = QListWidget()
        tl.addWidget(QLabel("ABOUT")); tl.addWidget(self.about_tasks); tl.addWidget(QLabel("USES")); tl.addWidget(self.uses_tasks); tl.addWidget(QLabel("REQUIRES")); tl.addWidget(self.requires_tasks)
        row = QHBoxLayout(); self.asset_new_task = QPushButton("New task"); self.asset_link_task = QPushButton("Link existing"); self.asset_unlink_task = QPushButton("Unlink")
        row.addWidget(self.asset_new_task); row.addWidget(self.asset_link_task); row.addWidget(self.asset_unlink_task); tl.addLayout(row)
        self.asset_tab.addTab(ttab, "Tasks")
        self.asset_save_btn.clicked.connect(self._save_asset)

    def refresh(self) -> None:
        rooms = self.task_service.list_rooms()
        room_name_by_id = {room.id: room.name for room in rooms}

        self.primary_room.clear()
        self.room_filter.blockSignals(True)
        current_filter = self.room_filter.currentData()
        self.room_filter.clear(); self.room_filter.addItem("all rooms", None)
        for room in rooms:
            self.primary_room.addItem(room.name, room.id)
            self.room_filter.addItem(room.name, room.id)
        if current_filter:
            idx = self.room_filter.findData(current_filter)
            if idx >= 0:
                self.room_filter.setCurrentIndex(idx)
        self.room_filter.blockSignals(False)

        self.asset_category.blockSignals(True)
        self.asset_category_edit.blockSignals(True)
        self.asset_category.clear(); self.asset_category.addItem("any")
        self.asset_category_edit.clear()
        categories = sorted({a.category for a in self.task_service.list_assets()})
        for category in categories:
            self.asset_category.addItem(category)
            self.asset_category_edit.addItem(category)
        self.asset_category.blockSignals(False)
        self.asset_category_edit.blockSignals(False)

        selected_room = self.room_filter.currentData()
        rows: list[AssetListRow] = []
        source_rooms = [selected_room] if selected_room else [room.id for room in rooms]
        for room_id in source_rooms:
            rows.extend(
                self.asset_service.list_assets_for_room(
                    room_id,
                    category=self.asset_category.currentText(),
                    warranty_soon=self.warranty_soon.isChecked(),
                    portable_only=self.portable_only.isChecked(),
                )
            )
        dedup: dict[str, AssetListRow] = {row.id: row for row in rows}
        filtered = [r for r in dedup.values() if self.asset_search.text().strip().lower() in r.name.lower()]
        filtered.sort(key=lambda r: r.name.lower())

        self._asset_rows = filtered
        self.assets_model.set_rows([(a.name, a.category, "Yes" if a.is_fixed else "No", a.warranty_expiry or "-", a.value or "-", "★" if a.is_primary_in_room else "") for a in filtered])
        self.assets_table.resizeColumnsToContents()
        self._room_name_by_id = room_name_by_id
        if self.current_asset_id and not any(asset.id == self.current_asset_id for asset in filtered):
            self.current_asset_id = None
            self.delete_asset_btn.setEnabled(False)

    def _select_asset(self, asset_id: str | None) -> None:
        if not asset_id:
            return
        for index, asset in enumerate(getattr(self, "_asset_rows", [])):
            if asset.id == asset_id:
                self.assets_table.selectRow(index)
                self._asset_selected()
                return

    def _asset_selected(self):
        selected = self.assets_table.selectionModel().selectedRows()
        if not selected:
            return
        asset = self._asset_rows[selected[0].row()]
        self.current_asset_id = asset.id
        self.delete_asset_btn.setEnabled(True)
        full = next((a for a in self.task_service.list_assets() if a.id == asset.id), None)
        if full:
            self.asset_name.setText(full.name); self.asset_category_edit.setCurrentText(full.category); self.asset_fixed.setChecked("portable" not in (full.notes or "").lower()); self.asset_notes.setText(full.notes or "")
            room_index = self.primary_room.findData(full.room_id)
            if room_index >= 0:
                self.primary_room.setCurrentIndex(room_index)
            self.asset_metadata.rebuild(category_id=full.category_id, owner_id=asset.id)

        links = self.task_service.list_task_links_for_asset(asset.id)
        self.about_tasks.clear(); self.about_tasks.addItems([t.title for t in links[LinkRole.ABOUT]])
        self.uses_tasks.clear(); self.uses_tasks.addItems([t.title for t in links[LinkRole.USES]])
        self.requires_tasks.clear(); self.requires_tasks.addItems([t.title for t in links[LinkRole.REQUIRES]])

    def _add_asset(self):
        rooms = [(room.id, room.name) for room in self.task_service.list_rooms()]
        if not rooms:
            QMessageBox.warning(self, "Validation", "Create at least one room before adding an asset")
            return
        categories = [self.asset_category.itemText(i) for i in range(self.asset_category.count()) if self.asset_category.itemText(i) != "any"]
        dialog = AddAssetDialog(rooms=rooms, categories=categories, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return
        if not dialog.name.text().strip():
            QMessageBox.warning(self, "Validation", "Asset name required")
            return
        if not dialog.primary_room.currentData():
            QMessageBox.warning(self, "Validation", "Primary room is required")
            return
        try:
            asset = self.asset_service.save_asset(
                AssetSaveDTO(
                    name=dialog.name.text(),
                    category=dialog.category.currentText(),
                    primary_room_id=dialog.primary_room.currentData(),
                    notes=dialog.notes.toPlainText(),
                )
            )
            self.task_service.session.commit()
            self.refresh(); self._select_asset(asset.id); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))

    def _save_asset(self):
        if not self.asset_name.text().strip():
            QMessageBox.warning(self, "Validation", "Asset name required")
            return
        if not self.primary_room.currentData():
            QMessageBox.warning(self, "Validation", "Primary room is required")
            return
        try:
            asset = self.asset_service.save_asset(AssetSaveDTO(id=self.current_asset_id, name=self.asset_name.text(), category=self.asset_category_edit.currentText(), primary_room_id=self.primary_room.currentData(), notes=self.asset_notes.toPlainText()))
            self.asset_metadata.persist_values(asset.id)
            self.task_service.session.commit()
            self.refresh(); self._select_asset(asset.id); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))

    def _delete_asset(self):
        if not self.current_asset_id:
            QMessageBox.information(self, "Delete asset", "Select an asset to delete")
            return
        selected = self.assets_table.selectionModel().selectedRows()
        asset_name = self._asset_rows[selected[0].row()].name if selected else "this asset"
        answer = QMessageBox.question(
            self,
            "Delete asset",
            f"Delete asset '{asset_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.asset_service.delete_asset(self.current_asset_id)
            self.task_service.session.commit()
            self.current_asset_id = None
            self.delete_asset_btn.setEnabled(False)
            self.refresh(); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Delete failed", str(exc))


class RoomsAssetsPage(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.rooms_tab = RoomsTab(task_service, on_data_changed)
        self.assets_tab = AssetsTab(task_service, on_data_changed)
        self.tabs.addTab(self.rooms_tab, "Rooms")
        self.tabs.addTab(self.assets_tab, "Assets")
        self.tabs.currentChanged.connect(self._refresh_current_tab)
        layout.addWidget(self.tabs)

    def _refresh_current_tab(self, index: int) -> None:
        if index == 0:
            self.rooms_tab.refresh()
        elif index == 1:
            self.assets_tab.refresh()

    def refresh(self) -> None:
        self._refresh_current_tab(self.tabs.currentIndex())


class RoomsAssetsPanel(RoomsAssetsPage):
    pass
