from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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


class RoomsAssetsPanel(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.room_service = RoomService(task_service)
        self.asset_service = AssetService(task_service)
        self.on_data_changed = on_data_changed
        self.current_room_id: str | None = None
        self.current_asset_id: str | None = None

        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        left = QWidget(); l = QVBoxLayout(left)
        f = QHBoxLayout(); self.room_search = QLineEdit(); self.room_type = QComboBox(); self.room_type.addItems(["any", "kitchen", "bathroom", "bedroom", "hall", "outdoor"])
        f.addWidget(self.room_search); f.addWidget(self.room_type); l.addLayout(f)
        self.rooms_model = SimpleTableModel(["Name", "Type", "Floor", "Asset count", "Open tasks", "Overdue tasks"])
        self.rooms_table = QTableView(); self.rooms_table.setModel(self.rooms_model); l.addWidget(self.rooms_table)

        middle = QWidget(); m = QVBoxLayout(middle)
        af = QHBoxLayout(); self.asset_category = QComboBox(); self.asset_category.addItem("any"); self.warranty_soon = QCheckBox("Warranty soon"); self.portable_only = QCheckBox("Portable only")
        af.addWidget(self.asset_category); af.addWidget(self.warranty_soon); af.addWidget(self.portable_only); m.addLayout(af)
        self.assets_model = SimpleTableModel(["Name", "Category", "Fixed", "Warranty", "Value", "Primary"])
        self.assets_table = QTableView(); self.assets_table.setModel(self.assets_model); m.addWidget(self.assets_table)

        right = QWidget(); r = QVBoxLayout(right)
        self.details_tabs = QTabWidget(); r.addWidget(self.details_tabs)
        self._build_room_tabs(); self._build_asset_tabs()
        for text in ["Asset reminders (coming soon)", "Reports: spend per room/category (coming soon)"]:
            lbl = QLabel(text); lbl.setEnabled(False); r.addWidget(lbl)

        splitter.addWidget(left); splitter.addWidget(middle); splitter.addWidget(right); splitter.setSizes([420, 420, 680])

        self.room_search.textChanged.connect(self.refresh)
        self.room_type.currentIndexChanged.connect(self.refresh)
        self.rooms_table.selectionModel().selectionChanged.connect(self._room_selected)
        self.assets_table.selectionModel().selectionChanged.connect(self._asset_selected)
        self.asset_category.currentIndexChanged.connect(self._refresh_assets)
        self.warranty_soon.stateChanged.connect(self._refresh_assets)
        self.portable_only.stateChanged.connect(self._refresh_assets)

        self.refresh()

    def _build_room_tabs(self):
        self.room_tab = QTabWidget()
        basics = QWidget(); form = QFormLayout(basics)
        self.room_name = QLineEdit(); self.room_type_edit = QComboBox(); self.room_type_edit.addItems(["any", "kitchen", "bathroom", "bedroom", "hall", "outdoor"])
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
        self.details_tabs.addTab(self.room_tab, "Room details")
        self.room_save_btn.clicked.connect(self._save_room)

    def _build_asset_tabs(self):
        self.asset_tab = QTabWidget()
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
        self.details_tabs.addTab(self.asset_tab, "Asset details")
        self.asset_save_btn.clicked.connect(self._save_asset)

    def refresh(self) -> None:
        rows = self.room_service.list_rooms_overview(search=self.room_search.text(), room_type=self.room_type.currentText())
        self._room_rows: list[RoomListRow] = rows
        self.rooms_model.set_rows([(r.name, r.room_type, r.floor_level or "-", r.asset_count, r.open_tasks_count, r.overdue_tasks_count) for r in rows])
        self.rooms_table.resizeColumnsToContents()

        self.primary_room.clear(); self.asset_category.clear(); self.asset_category.addItem("any"); self.asset_category_edit.clear()
        categories = sorted({a.category for a in self.task_service.list_assets()})
        for c in categories:
            self.asset_category.addItem(c); self.asset_category_edit.addItem(c)
        for room in self.task_service.list_rooms():
            self.primary_room.addItem(room.name, room.id)

        if rows:
            self.rooms_table.selectRow(0)
            self._room_selected()

    def _refresh_assets(self):
        if not self.current_room_id:
            self.assets_model.set_rows([])
            return
        rows = self.asset_service.list_assets_for_room(
            self.current_room_id,
            category=self.asset_category.currentText(),
            warranty_soon=self.warranty_soon.isChecked(),
            portable_only=self.portable_only.isChecked(),
        )
        self._asset_rows: list[AssetListRow] = rows
        self.assets_model.set_rows([(a.name, a.category, "Yes" if a.is_fixed else "No", a.warranty_expiry or "-", a.value or "-", "★" if a.is_primary_in_room else "") for a in rows])
        self.assets_table.resizeColumnsToContents()

    def _room_selected(self):
        selected = self.rooms_table.selectionModel().selectedRows()
        if not selected:
            return
        room = self._room_rows[selected[0].row()]
        self.current_room_id = room.id
        full = next((r for r in self.task_service.list_rooms() if r.id == room.id), None)
        if full:
            self.room_name.setText(full.name); self.room_type_edit.setCurrentText(full.description or "any"); self.room_floor.setText(full.floor_level or ""); self.room_notes.setText(full.notes or "")
            self.room_metadata.rebuild(room_type=full.description or "any", owner_id=room.id)
        direct, derived = self.task_service.list_task_titles_for_room(room.id)
        self.room_direct_tasks.clear(); self.room_direct_tasks.addItems([t.title for t in direct])
        self.room_derived_tasks.clear(); self.room_derived_tasks.addItems([t.title for t in derived])
        self._refresh_assets()
        self.details_tabs.setCurrentIndex(0)

    def _asset_selected(self):
        selected = self.assets_table.selectionModel().selectedRows()
        if not selected:
            return
        asset = self._asset_rows[selected[0].row()]
        self.current_asset_id = asset.id
        full = next((a for a in self.task_service.list_assets() if a.id == asset.id), None)
        if full:
            self.asset_name.setText(full.name); self.asset_category_edit.setCurrentText(full.category); self.asset_fixed.setChecked("portable" not in (full.notes or "").lower()); self.asset_notes.setText(full.notes or "")
            self.asset_metadata.rebuild(category_id=full.category_id, owner_id=asset.id)

        links = self.task_service.list_task_links_for_asset(asset.id)
        self.about_tasks.clear(); self.about_tasks.addItems([t.title for t in links[LinkRole.ABOUT]])
        self.uses_tasks.clear(); self.uses_tasks.addItems([t.title for t in links[LinkRole.USES]])
        self.requires_tasks.clear(); self.requires_tasks.addItems([t.title for t in links[LinkRole.REQUIRES]])
        self.details_tabs.setCurrentIndex(1)

    def _save_room(self):
        if not self.room_name.text().strip():
            QMessageBox.warning(self, "Validation", "Room name required")
            return
        try:
            room = self.room_service.save_room(RoomSaveDTO(id=self.current_room_id, name=self.room_name.text(), room_type=self.room_type_edit.currentText(), floor_level=self.room_floor.text(), notes=self.room_notes.toPlainText()))
            self.room_metadata.persist_values(room.id)
            self.task_service.session.commit()
            self.refresh(); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))

    def _save_asset(self):
        if not self.asset_name.text().strip():
            QMessageBox.warning(self, "Validation", "Asset name required")
            return
        try:
            asset = self.asset_service.save_asset(AssetSaveDTO(id=self.current_asset_id, name=self.asset_name.text(), category=self.asset_category_edit.currentText(), primary_room_id=self.primary_room.currentData(), notes=self.asset_notes.toPlainText()))
            self.asset_metadata.persist_values(asset.id)
            self.task_service.session.commit()
            self.refresh(); self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback(); QMessageBox.warning(self, "Save failed", str(exc))
