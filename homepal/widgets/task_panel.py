from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from homepal.models import LinkRole, Priority, TaskStatus
from homepal.services.task_service import TaskEditorDTO, TaskListFilters, TaskListRow, TaskService


class TaskTableModel(QAbstractTableModel):
    HEADERS = ["Title", "Priority", "Status", "Due", "Rooms", "About assets", "Flags", "Updated"]

    def __init__(self):
        super().__init__()
        self.rows: list[TaskListRow] = []

    def set_rows(self, rows: list[TaskListRow]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        values = [
            row.title,
            row.priority.value,
            row.status.value,
            row.due_date.strftime("%Y-%m-%d %H:%M") if row.due_date else "-",
            str(row.room_count),
            str(row.about_asset_count),
            ", ".join([x for x in ["Urgent" if row.is_urgent else "", "Follow-up" if row.requires_follow_up else ""] if x]) or "-",
            row.updated_at.strftime("%Y-%m-%d %H:%M"),
        ]
        return values[index.column()]


class TaskPanel(QWidget):
    data_changed = Signal()

    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service
        self._dirty = False
        self._current_task_id: str | None = None

        root = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        filter_row = QHBoxLayout()

        self.status_filter = QComboBox(); self.status_filter.addItem("Any status", [])
        for st in TaskStatus:
            self.status_filter.addItem(st.value, [st])
        self.priority_filter = QComboBox(); self.priority_filter.addItem("Any priority", [])
        for p in Priority:
            self.priority_filter.addItem(p.value, [p])
        self.due_filter = QComboBox(); self.due_filter.addItems(["Any", "Overdue", "Next 7 days", "Next 30 days"])
        self.room_filter = QComboBox(); self.asset_filter = QComboBox()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search title/description")
        for widget in [self.status_filter, self.priority_filter, self.due_filter, self.room_filter, self.asset_filter, self.search_input]:
            filter_row.addWidget(widget)
        left_layout.addLayout(filter_row)

        self.model = TaskTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        left_layout.addWidget(self.table)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        top = QHBoxLayout(); self.new_btn = QPushButton("New task"); self.save_btn = QPushButton("Save"); self.discard_btn = QPushButton("Discard"); self.delete_btn = QPushButton("Delete")
        top.addWidget(self.new_btn); top.addWidget(self.save_btn); top.addWidget(self.discard_btn); top.addWidget(self.delete_btn); top.addStretch(1)
        right_layout.addLayout(top)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)
        self._build_summary_tab(); self._build_rooms_tab(); self._build_assets_tab(); self._build_stub_tab("Recurrence", "Recurrence editor (coming soon)")
        self._build_stub_tab("Documents", "Attachments and receipt workflow (coming soon)")

        for text in [
            "Calendar view (coming soon)",
            "Templates (coming soon)",
            "Photo capture workflow (coming soon)",
            "Advanced search including attributes (coming soon)",
        ]:
            lbl = QLabel(text); lbl.setEnabled(False); right_layout.addWidget(lbl)

        splitter.addWidget(left); splitter.addWidget(right); splitter.setSizes([760, 760])

        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.priority_filter.currentIndexChanged.connect(self.refresh)
        self.due_filter.currentIndexChanged.connect(self.refresh)
        self.room_filter.currentIndexChanged.connect(self.refresh)
        self.asset_filter.currentIndexChanged.connect(self.refresh)
        self.search_input.textChanged.connect(self.refresh)
        self.table.selectionModel().selectionChanged.connect(self._on_selected)
        self.new_btn.clicked.connect(self._start_new)
        self.save_btn.clicked.connect(self._save)
        self.discard_btn.clicked.connect(self._discard)
        self.delete_btn.clicked.connect(self._delete_task)

        self._reload_pickers()
        self._start_new()
        self.refresh()

    def _build_summary_tab(self):
        tab = QWidget(); form = QFormLayout(tab)
        self.title_input = QLineEdit(); self.desc_input = QTextEdit(); self.priority_input = QComboBox(); self.status_input = QComboBox()
        self.due_input = QDateTimeEdit(); self.due_input.setCalendarPopup(True); self.due_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_input.setDateTime(datetime.now())
        self.est_cost_input = QLineEdit(); self.actual_cost_input = QLineEdit(); self.effort_input = QLineEdit(); self.follow_input = QCheckBox("Follow-up needed")
        for p in Priority: self.priority_input.addItem(p.value, p)
        for s in TaskStatus: self.status_input.addItem(s.value, s)
        for lbl, field in [("Title", self.title_input), ("Description", self.desc_input), ("Priority", self.priority_input), ("Status", self.status_input), ("Due", self.due_input), ("Estimated cost", self.est_cost_input), ("Actual cost", self.actual_cost_input), ("Effort (hours)", self.effort_input), ("", self.follow_input)]:
            form.addRow(lbl, field)
        self.tabs.addTab(tab, "Summary")
        self.status_input.currentIndexChanged.connect(self._toggle_actual_cost)

    def _build_rooms_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.rooms_selected = QListWidget(); layout.addWidget(QLabel("Rooms")); layout.addWidget(self.rooms_selected)
        row = QHBoxLayout(); self.room_picker = QComboBox(); self.add_room_btn = QPushButton("Add room"); self.quick_room_btn = QPushButton("Create Room")
        row.addWidget(self.room_picker); row.addWidget(self.add_room_btn); row.addWidget(self.quick_room_btn); layout.addLayout(row)
        self.add_primary_btn = QPushButton("Add primary rooms from ABOUT assets")
        layout.addWidget(self.add_primary_btn)
        self.tabs.addTab(tab, "Rooms")
        self.add_room_btn.clicked.connect(lambda: self._add_to_list(self.room_picker, self.rooms_selected))
        self.quick_room_btn.clicked.connect(self._quick_add_room)
        self.add_primary_btn.clicked.connect(self._suggest_primary_rooms)

    def _build_assets_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.about_selected = QListWidget(); self.uses_selected = QListWidget(); self.requires_selected = QListWidget()
        for label, picker_name, button_name, list_widget, quick_fn in [
            ("ABOUT assets", "about_picker", "add_about_btn", self.about_selected, self._quick_add_asset),
            ("USES assets", "uses_picker", "add_uses_btn", self.uses_selected, self._quick_add_asset),
        ]:
            layout.addWidget(QLabel(label)); layout.addWidget(list_widget)
            row = QHBoxLayout(); picker = QComboBox(); setattr(self, picker_name, picker); add_btn = QPushButton("Add"); setattr(self, button_name, add_btn)
            create_btn = QPushButton("Create asset")
            row.addWidget(picker); row.addWidget(add_btn); row.addWidget(create_btn); layout.addLayout(row)
            add_btn.clicked.connect(lambda _=False, p=picker, l=list_widget: self._add_to_list(p, l))
            create_btn.clicked.connect(quick_fn)
        layout.addWidget(QLabel("REQUIRES assets (quantity unit)")); layout.addWidget(self.requires_selected)
        self.require_picker = QComboBox(); self.require_qty = QLineEdit(); self.require_unit = QLineEdit(); self.add_require_btn = QPushButton("Add required material")
        req = QHBoxLayout(); req.addWidget(self.require_picker); req.addWidget(self.require_qty); req.addWidget(self.require_unit); req.addWidget(self.add_require_btn)
        layout.addLayout(req)
        self.quick_material_btn = QPushButton("Create Required Material")
        layout.addWidget(self.quick_material_btn)
        self.tabs.addTab(tab, "Assets")
        self.add_require_btn.clicked.connect(self._add_requires)
        self.quick_material_btn.clicked.connect(self._quick_add_asset)

    def _build_stub_tab(self, title: str, text: str):
        tab = QWidget(); lay = QVBoxLayout(tab); lbl = QLabel(text); lbl.setEnabled(False); lay.addWidget(lbl)
        self.tabs.addTab(tab, title)

    def _toggle_actual_cost(self):
        completed = self.status_input.currentData() == TaskStatus.COMPLETED
        self.actual_cost_input.setEnabled(completed)

    def _reload_pickers(self):
        rooms = self.task_service.list_rooms()
        assets = self.task_service.list_assets()
        self.room_filter.clear(); self.room_filter.addItem("Any room", None)
        self.asset_filter.clear(); self.asset_filter.addItem("Any asset", None)
        self.room_picker.clear(); self.about_picker.clear(); self.uses_picker.clear(); self.require_picker.clear()
        for room in rooms:
            self.room_filter.addItem(room.name, room.id); self.room_picker.addItem(room.name, room.id)
        for asset in assets:
            self.asset_filter.addItem(asset.name, asset.id)
            for picker in [self.about_picker, self.uses_picker, self.require_picker]:
                picker.addItem(asset.name, asset.id)

    def _add_to_list(self, combo: QComboBox, target: QListWidget):
        text = combo.currentText(); key = combo.currentData()
        if not key:
            return
        for i in range(target.count()):
            if target.item(i).data(Qt.UserRole) == key:
                return
        it = QListWidgetItem(text); it.setData(Qt.UserRole, key); target.addItem(it); self._dirty = True

    def _add_requires(self):
        asset_id = self.require_picker.currentData();
        if not asset_id:
            return
        label = f"{self.require_picker.currentText()} | {self.require_qty.text().strip() or '-'} {self.require_unit.text().strip()}".strip()
        it = QListWidgetItem(label)
        it.setData(Qt.UserRole, (asset_id, self.require_qty.text().strip(), self.require_unit.text().strip() or None))
        self.requires_selected.addItem(it)
        self._dirty = True

    def _collect(self) -> TaskEditorDTO:
        def decimal_or_none(txt: str):
            if not txt.strip():
                return None
            try:
                return Decimal(txt.strip())
            except InvalidOperation:
                raise ValueError(f"Invalid decimal: {txt}")

        requires = []
        for i in range(self.requires_selected.count()):
            asset_id, qty, unit = self.requires_selected.item(i).data(Qt.UserRole)
            requires.append((asset_id, Decimal(qty) if qty else None, unit))

        return TaskEditorDTO(
            id=self._current_task_id,
            title=self.title_input.text(),
            description=self.desc_input.toPlainText(),
            priority=self.priority_input.currentData(),
            status=self.status_input.currentData(),
            due_date=self.due_input.dateTime().toPython() if self.due_input.dateTime().isValid() else None,
            estimated_cost=decimal_or_none(self.est_cost_input.text()),
            actual_cost=decimal_or_none(self.actual_cost_input.text()) if self.actual_cost_input.isEnabled() else None,
            effort_hours=decimal_or_none(self.effort_input.text()),
            follow_up_needed=self.follow_input.isChecked(),
            room_ids=[self.rooms_selected.item(i).data(Qt.UserRole) for i in range(self.rooms_selected.count())],
            about_asset_ids=[self.about_selected.item(i).data(Qt.UserRole) for i in range(self.about_selected.count())],
            uses_asset_ids=[self.uses_selected.item(i).data(Qt.UserRole) for i in range(self.uses_selected.count())],
            requires_assets=requires,
        )

    def _apply(self, dto: TaskEditorDTO):
        self._current_task_id = dto.id
        self.title_input.setText(dto.title); self.desc_input.setText(dto.description)
        self.priority_input.setCurrentIndex(max(0, self.priority_input.findData(dto.priority)))
        self.status_input.setCurrentIndex(max(0, self.status_input.findData(dto.status)))
        if dto.due_date:
            self.due_input.setDateTime(dto.due_date)
        else:
            self.due_input.setDateTime(datetime.now())
        self.est_cost_input.setText(str(dto.estimated_cost or "")); self.actual_cost_input.setText(str(dto.actual_cost or "")); self.effort_input.setText(str(dto.effort_hours or ""))
        self.follow_input.setChecked(dto.follow_up_needed)
        for lst in [self.rooms_selected, self.about_selected, self.uses_selected, self.requires_selected]:
            lst.clear()
        room_names = {r.id: r.name for r in self.task_service.list_rooms()}; asset_names = {a.id: a.name for a in self.task_service.list_assets()}
        for rid in dto.room_ids:
            it = QListWidgetItem(room_names.get(rid, rid)); it.setData(Qt.UserRole, rid); self.rooms_selected.addItem(it)
        for aid in dto.about_asset_ids:
            it = QListWidgetItem(asset_names.get(aid, aid)); it.setData(Qt.UserRole, aid); self.about_selected.addItem(it)
        for aid in dto.uses_asset_ids:
            it = QListWidgetItem(asset_names.get(aid, aid)); it.setData(Qt.UserRole, aid); self.uses_selected.addItem(it)
        for aid, qty, unit in dto.requires_assets:
            it = QListWidgetItem(f"{asset_names.get(aid, aid)} | {qty or '-'} {unit or ''}"); it.setData(Qt.UserRole, (aid, str(qty) if qty is not None else "", unit)); self.requires_selected.addItem(it)
        self._toggle_actual_cost(); self._dirty = False

    def _start_new(self):
        if not self._confirm_navigation_if_dirty():
            return
        self._apply(TaskEditorDTO())

    def _discard(self):
        if self._current_task_id:
            self._apply(self.task_service.get_task_editor_dto(self._current_task_id))
        else:
            self._apply(TaskEditorDTO())


    def _delete_task(self):
        if not self._current_task_id:
            return
        answer = QMessageBox.question(self, "Delete task", "Delete current task?")
        if answer != QMessageBox.Yes:
            return
        try:
            self.task_service.delete_task(self._current_task_id)
            self.task_service.session.commit()
            self._current_task_id = None
            self._apply(TaskEditorDTO())
            self.refresh(); self.data_changed.emit()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Delete failed", str(exc))

    def _save(self):
        try:
            dto = self._collect()
            if not dto.title.strip():
                raise ValueError("Title is required")
            if not dto.room_ids and not dto.about_asset_ids:
                raise ValueError("Select at least one room or ABOUT asset")
            task = self.task_service.save_task_editor_dto(dto)
            self.task_service.session.commit()
            self._current_task_id = task.id
            self._dirty = False
            self.refresh(); self.data_changed.emit()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Save failed", str(exc))

    def _on_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        row = self.model.rows[selected[0].row()]
        if self._current_task_id == row.id:
            return
        if not self._confirm_navigation_if_dirty():
            return
        self._apply(self.task_service.get_task_editor_dto(row.id))

    def _confirm_navigation_if_dirty(self) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(self, "Unsaved changes", "You have unsaved edits. Discard them?")
        return answer == QMessageBox.Yes

    def _suggest_primary_rooms(self):
        about_ids = [self.about_selected.item(i).data(Qt.UserRole) for i in range(self.about_selected.count())]
        room_ids = self.task_service.suggest_primary_rooms_from_about_assets(about_ids)
        by_id = {r.id: r.name for r in self.task_service.list_rooms()}
        for rid in room_ids:
            fake = QComboBox(); fake.addItem(by_id.get(rid, rid), rid); fake.setCurrentIndex(0)
            self._add_to_list(fake, self.rooms_selected)

    def _quick_add_room(self):
        name = f"Room {self.room_picker.count() + 1}"
        room = self.task_service.create_room(name=name)
        self.task_service.session.flush(); self._reload_pickers()
        self.room_picker.setCurrentIndex(self.room_picker.findData(room.id)); self._add_to_list(self.room_picker, self.rooms_selected)

    def _quick_add_asset(self):
        if self.room_picker.count() == 0:
            QMessageBox.warning(self, "No rooms", "Create a room first.")
            return
        room_id = self.room_picker.currentData()
        asset = self.task_service.create_asset(primary_room_id=room_id, name=f"Asset {self.about_picker.count()+1}", category="General")
        self.task_service.session.flush(); self._reload_pickers()
        for picker in [self.about_picker, self.uses_picker, self.require_picker]:
            picker.setCurrentIndex(picker.findData(asset.id))

    def refresh(self) -> None:
        filters = TaskListFilters(
            statuses=self.status_filter.currentData() or [],
            priorities=self.priority_filter.currentData() or [],
            due_range={"Any": "any", "Overdue": "overdue", "Next 7 days": "next7", "Next 30 days": "next30"}[self.due_filter.currentText()],
            room_id=self.room_filter.currentData(),
            asset_id=self.asset_filter.currentData(),
            search=self.search_input.text(),
        )
        self.model.set_rows(self.task_service.list_task_rows(filters))
        self.table.resizeColumnsToContents()
