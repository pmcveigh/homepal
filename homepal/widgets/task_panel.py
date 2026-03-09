from __future__ import annotations

from datetime import datetime
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

from homepal.models import Priority, RecurrenceType, TaskStatus
from homepal.services.task_service import TaskEditorDTO, TaskListFilters, TaskListRow, TaskService


class TaskTableModel(QAbstractTableModel):
    HEADERS = ["Title", "Priority", "Status", "Due", "Room", "Assignees", "Providers", "Flags", "Updated"]

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
            row.room_name or "-",
            ", ".join(row.assignee_names) or "-",
            ", ".join(row.provider_names) or "-",
            ", ".join([x for x in ["OVERDUE" if row.is_overdue else "", "Due today" if row.is_due_today else "", "Urgent" if row.is_urgent else "", "Follow-up" if row.requires_follow_up else ""] if x]) or "-",
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
        for priority in Priority:
            self.priority_filter.addItem(priority.value, [priority])
        self.due_filter = QComboBox(); self.due_filter.addItems(["Any", "Overdue", "Due today", "Due this week", "Next 7 days", "Next 30 days"])
        self.room_filter = QComboBox(); self.asset_filter = QComboBox()
        self.member_filter = QComboBox(); self.provider_filter = QComboBox()
        self.sort_filter = QComboBox(); self.sort_filter.addItems(["Recently updated", "Priority", "Due date", "Room", "Assignee"])
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Search title/description")
        for widget in [self.status_filter, self.priority_filter, self.due_filter, self.room_filter, self.asset_filter, self.member_filter, self.provider_filter, self.sort_filter, self.search_input]:
            filter_row.addWidget(widget)
        left_layout.addLayout(filter_row)

        self.model = TaskTableModel()
        self.view_tabs = QTabWidget()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.kanban_list = QListWidget()
        self.calendar_list = QListWidget()
        self.grouped_list = QListWidget()
        self.view_tabs.addTab(self.table, "List")
        self.view_tabs.addTab(self.kanban_list, "Kanban")
        self.view_tabs.addTab(self.calendar_list, "Calendar")
        self.view_tabs.addTab(self.grouped_list, "Grouped")
        left_layout.addWidget(self.view_tabs)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        button_row = QHBoxLayout()
        self.new_btn = QPushButton("New task")
        self.duplicate_btn = QPushButton("Duplicate")
        self.template_btn = QPushButton("Save as template")
        self.generate_btn = QPushButton("Generate recurring")
        self.save_btn = QPushButton("Save")
        self.discard_btn = QPushButton("Discard")
        self.delete_btn = QPushButton("Delete")
        for button in [self.new_btn, self.duplicate_btn, self.template_btn, self.generate_btn, self.save_btn, self.discard_btn, self.delete_btn]:
            button_row.addWidget(button)
        button_row.addStretch(1)
        right_layout.addLayout(button_row)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs)
        self._build_summary_tab()
        self._build_rooms_tab()
        self._build_assets_tab()
        self._build_people_tab()
        self._build_materials_tab()
        self._build_checklist_tab()
        self._build_dependencies_tab()
        self._build_recurrence_tab()
        self._build_documents_tab()

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([760, 760])

        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.priority_filter.currentIndexChanged.connect(self.refresh)
        self.due_filter.currentIndexChanged.connect(self.refresh)
        self.room_filter.currentIndexChanged.connect(self.refresh)
        self.asset_filter.currentIndexChanged.connect(self.refresh)
        self.member_filter.currentIndexChanged.connect(self.refresh)
        self.provider_filter.currentIndexChanged.connect(self.refresh)
        self.sort_filter.currentIndexChanged.connect(self.refresh)
        self.search_input.textChanged.connect(self.refresh)
        self.table.selectionModel().selectionChanged.connect(self._on_selected)
        self.new_btn.clicked.connect(self._start_new)
        self.duplicate_btn.clicked.connect(self._duplicate_current)
        self.template_btn.clicked.connect(self._save_template_copy)
        self.generate_btn.clicked.connect(self._generate_recurring)
        self.save_btn.clicked.connect(self._save)
        self.discard_btn.clicked.connect(self._discard)
        self.delete_btn.clicked.connect(self._delete_task)

        self._reload_pickers()
        self._start_new()
        self.refresh()

    def _build_summary_tab(self):
        tab = QWidget(); form = QFormLayout(tab)
        self.title_input = QLineEdit(); self.desc_input = QTextEdit()
        self.priority_input = QComboBox(); self.status_input = QComboBox()
        self.due_input = QDateTimeEdit(); self.due_input.setCalendarPopup(True); self.due_input.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.due_input.setDateTime(datetime.now())
        self.est_cost_input = QLineEdit(); self.actual_cost_input = QLineEdit(); self.effort_input = QLineEdit(); self.follow_input = QCheckBox("Follow-up needed"); self.template_input = QCheckBox("Template task")
        for priority in Priority:
            self.priority_input.addItem(priority.value, priority)
        for status in TaskStatus:
            self.status_input.addItem(status.value, status)
        for label, field in [("Title", self.title_input), ("Description", self.desc_input), ("Priority", self.priority_input), ("Status", self.status_input), ("Due", self.due_input), ("Estimated cost", self.est_cost_input), ("Actual cost", self.actual_cost_input), ("Effort (hours)", self.effort_input), ("", self.follow_input), ("", self.template_input)]:
            form.addRow(label, field)
        self.tabs.addTab(tab, "Summary")

    def _build_rooms_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.rooms_selected = QListWidget(); layout.addWidget(self.rooms_selected)
        row = QHBoxLayout()
        self.room_picker = QComboBox(); self.add_room_btn = QPushButton("Add room"); self.remove_room_btn = QPushButton("Remove selected")
        row.addWidget(self.room_picker); row.addWidget(self.add_room_btn); row.addWidget(self.remove_room_btn)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Rooms")
        self.add_room_btn.clicked.connect(lambda: self._add_to_list(self.room_picker, self.rooms_selected))
        self.remove_room_btn.clicked.connect(lambda: self._remove_current_item(self.rooms_selected))

    def _build_assets_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.required_assets = QListWidget(); layout.addWidget(self.required_assets)
        row = QHBoxLayout()
        self.required_picker = QComboBox(); self.required_purpose = QLineEdit(); self.required_purpose.setPlaceholderText("Purpose/notes")
        self.add_required_btn = QPushButton("Add"); self.remove_required_btn = QPushButton("Remove")
        for widget in [self.required_picker, self.required_purpose, self.add_required_btn, self.remove_required_btn]:
            row.addWidget(widget)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Assets")
        self.add_required_btn.clicked.connect(self._add_required_asset)
        self.remove_required_btn.clicked.connect(lambda: self._remove_current_item(self.required_assets))

    def _build_people_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.members_list = QListWidget(); self.members_list.setSelectionMode(QListWidget.MultiSelection)
        self.providers_list = QListWidget(); self.providers_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(QLabel("Assign household members")); layout.addWidget(self.members_list)
        layout.addWidget(QLabel("Link providers")); layout.addWidget(self.providers_list)
        self.tabs.addTab(tab, "People & Providers")

    def _build_materials_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.materials_list = QListWidget(); layout.addWidget(self.materials_list)
        row = QHBoxLayout()
        self.material_name_input = QLineEdit(); self.material_name_input.setPlaceholderText("Material")
        self.material_qty_input = QLineEdit(); self.material_qty_input.setPlaceholderText("Qty")
        self.material_unit_input = QLineEdit(); self.material_unit_input.setPlaceholderText("Unit")
        self.material_purchased_input = QCheckBox("Purchased")
        self.material_add_btn = QPushButton("Add/Update")
        self.material_remove_btn = QPushButton("Remove")
        for widget in [self.material_name_input, self.material_qty_input, self.material_unit_input, self.material_purchased_input, self.material_add_btn, self.material_remove_btn]:
            row.addWidget(widget)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Materials")
        self.material_add_btn.clicked.connect(self._add_material)
        self.material_remove_btn.clicked.connect(lambda: self._remove_current_item(self.materials_list))

    def _build_checklist_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.checklist = QListWidget(); layout.addWidget(self.checklist)
        row = QHBoxLayout()
        self.checklist_input = QLineEdit(); self.checklist_input.setPlaceholderText("Checklist item")
        self.checklist_done = QCheckBox("Done")
        self.checklist_add_btn = QPushButton("Add/Update")
        self.checklist_remove_btn = QPushButton("Remove")
        for widget in [self.checklist_input, self.checklist_done, self.checklist_add_btn, self.checklist_remove_btn]:
            row.addWidget(widget)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Checklist")
        self.checklist_add_btn.clicked.connect(self._add_checklist_item)
        self.checklist_remove_btn.clicked.connect(lambda: self._remove_current_item(self.checklist))

    def _build_dependencies_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.dependencies = QListWidget(); layout.addWidget(self.dependencies)
        row = QHBoxLayout()
        self.dependency_picker = QComboBox(); self.dep_add_btn = QPushButton("Add dependency"); self.dep_remove_btn = QPushButton("Remove")
        row.addWidget(self.dependency_picker); row.addWidget(self.dep_add_btn); row.addWidget(self.dep_remove_btn)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Dependencies")
        self.dep_add_btn.clicked.connect(lambda: self._add_to_list(self.dependency_picker, self.dependencies))
        self.dep_remove_btn.clicked.connect(lambda: self._remove_current_item(self.dependencies))

    def _build_recurrence_tab(self):
        tab = QWidget(); form = QFormLayout(tab)
        self.recurrence_type = QComboBox(); self.recurrence_type.addItem("None", None)
        for recurrence in RecurrenceType:
            self.recurrence_type.addItem(recurrence.value, recurrence)
        self.recurrence_interval = QLineEdit(); self.recurrence_interval.setPlaceholderText("Interval days (for custom)")
        form.addRow("Recurrence", self.recurrence_type)
        form.addRow("Interval", self.recurrence_interval)
        self.tabs.addTab(tab, "Recurrence")

    def _build_documents_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.attachments = QListWidget(); layout.addWidget(self.attachments)
        row = QHBoxLayout()
        self.attachment_input = QLineEdit(); self.attachment_input.setPlaceholderText("File path / URL")
        self.attach_add_btn = QPushButton("Add")
        self.attach_remove_btn = QPushButton("Remove")
        row.addWidget(self.attachment_input); row.addWidget(self.attach_add_btn); row.addWidget(self.attach_remove_btn)
        layout.addLayout(row)
        self.tabs.addTab(tab, "Documents")
        self.attach_add_btn.clicked.connect(self._add_attachment)
        self.attach_remove_btn.clicked.connect(lambda: self._remove_current_item(self.attachments))

    def _reload_pickers(self):
        rooms = self.task_service.list_rooms()
        assets = self.task_service.list_assets()
        providers = self.task_service.list_providers()
        members = self.task_service.list_household_members()
        tasks = self.task_service.list_tasks()

        self.room_filter.clear(); self.room_filter.addItem("Any room", None)
        self.asset_filter.clear(); self.asset_filter.addItem("Any asset", None)
        self.member_filter.clear(); self.member_filter.addItem("Any assignee", None)
        self.provider_filter.clear(); self.provider_filter.addItem("Any provider", None)
        self.room_picker.clear(); self.required_picker.clear(); self.dependency_picker.clear()

        for room in rooms:
            self.room_filter.addItem(room.name, room.id)
            self.room_picker.addItem(room.name, room.id)
        for asset in assets:
            self.asset_filter.addItem(asset.name, asset.id)
            self.required_picker.addItem(asset.name, asset.id)
        for task in tasks:
            self.dependency_picker.addItem(task.title, task.id)

        self.members_list.clear()
        for member in members:
            self.member_filter.addItem(member.name, member.id)
            item = QListWidgetItem(member.name)
            item.setData(Qt.UserRole, member.id)
            self.members_list.addItem(item)

        self.providers_list.clear()
        for provider in providers:
            self.provider_filter.addItem(provider.name, provider.id)
            item = QListWidgetItem(f"{provider.name} ({provider.service_type})")
            item.setData(Qt.UserRole, provider.id)
            self.providers_list.addItem(item)

    def refresh_topology(self) -> None:
        self._reload_pickers()

    def _add_to_list(self, combo: QComboBox, target: QListWidget):
        key = combo.currentData()
        if not key:
            return
        if key == self._current_task_id:
            return
        for i in range(target.count()):
            if target.item(i).data(Qt.UserRole) == key:
                return
        item = QListWidgetItem(combo.currentText())
        item.setData(Qt.UserRole, key)
        target.addItem(item)
        self._dirty = True

    def _remove_current_item(self, target: QListWidget):
        row = target.currentRow()
        if row >= 0:
            target.takeItem(row)
            self._dirty = True

    def _add_required_asset(self):
        asset_id = self.required_picker.currentData()
        if not asset_id:
            return
        purpose = self.required_purpose.text().strip() or None
        for i in range(self.required_assets.count()):
            old_id, _ = self.required_assets.item(i).data(Qt.UserRole)
            if old_id == asset_id:
                self.required_assets.item(i).setData(Qt.UserRole, (asset_id, purpose))
                self.required_assets.item(i).setText(self._required_asset_label(self.required_picker.currentText(), purpose))
                self._dirty = True
                return
        item = QListWidgetItem(self._required_asset_label(self.required_picker.currentText(), purpose))
        item.setData(Qt.UserRole, (asset_id, purpose))
        self.required_assets.addItem(item)
        self._dirty = True

    def _required_asset_label(self, name: str, purpose: str | None) -> str:
        return f"{name} — {purpose}" if purpose else name

    def _add_material(self):
        name = self.material_name_input.text().strip()
        if not name:
            return
        quantity = self._decimal_or_none(self.material_qty_input.text())
        unit = self.material_unit_input.text().strip() or None
        purchased = self.material_purchased_input.isChecked()
        data = (name, quantity, unit, purchased)
        label = self._material_label(*data)
        for i in range(self.materials_list.count()):
            item = self.materials_list.item(i)
            if item.data(Qt.UserRole)[0].lower() == name.lower():
                item.setData(Qt.UserRole, data)
                item.setText(label)
                self._dirty = True
                return
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, data)
        self.materials_list.addItem(item)
        self._dirty = True

    def _material_label(self, name: str, quantity: Decimal | None, unit: str | None, purchased: bool) -> str:
        qty_txt = f"{quantity} {unit or ''}".strip() if quantity is not None else (unit or "")
        prefix = "✅" if purchased else "🛒"
        return f"{prefix} {name}" + (f" ({qty_txt})" if qty_txt else "")

    def _add_checklist_item(self):
        label = self.checklist_input.text().strip()
        if not label:
            return
        done = self.checklist_done.isChecked()
        text = f"{'☑' if done else '☐'} {label}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, (label, done))
        self.checklist.addItem(item)
        self._dirty = True

    def _add_attachment(self):
        value = self.attachment_input.text().strip()
        if not value:
            return
        item = QListWidgetItem(value)
        item.setData(Qt.UserRole, value)
        self.attachments.addItem(item)
        self.attachment_input.clear()
        self._dirty = True

    def _collect(self) -> TaskEditorDTO:
        required_assets = [self.required_assets.item(i).data(Qt.UserRole) for i in range(self.required_assets.count())]
        material_rows = [self.materials_list.item(i).data(Qt.UserRole) for i in range(self.materials_list.count())]
        return TaskEditorDTO(
            id=self._current_task_id,
            title=self.title_input.text(),
            description=self.desc_input.toPlainText(),
            priority=self.priority_input.currentData(),
            status=self.status_input.currentData(),
            due_date=self.due_input.dateTime().toPython() if self.due_input.dateTime().isValid() else None,
            estimated_cost=self._decimal_or_none(self.est_cost_input.text()),
            actual_cost=self._decimal_or_none(self.actual_cost_input.text()),
            effort_hours=self._decimal_or_none(self.effort_input.text()),
            follow_up_needed=self.follow_input.isChecked(),
            room_ids=[self.rooms_selected.item(i).data(Qt.UserRole) for i in range(self.rooms_selected.count())],
            requires_assets=[(asset_id, None, purpose) for asset_id, purpose in required_assets],
            assigned_member_ids=[item.data(Qt.UserRole) for item in self.members_list.selectedItems()],
            provider_ids=[item.data(Qt.UserRole) for item in self.providers_list.selectedItems()],
            checklist_items=[self.checklist.item(i).data(Qt.UserRole) for i in range(self.checklist.count())],
            dependency_task_ids=[self.dependencies.item(i).data(Qt.UserRole) for i in range(self.dependencies.count())],
            required_materials=[(name, quantity, unit) for name, quantity, unit, _ in material_rows],
            purchased_material_labels=[name for name, _, _, purchased in material_rows if purchased],
            attachments=[self.attachments.item(i).data(Qt.UserRole) for i in range(self.attachments.count())],
            recurring_type=self.recurrence_type.currentData(),
            recurring_interval_days=int(self.recurrence_interval.text().strip()) if self.recurrence_interval.text().strip() else None,
            is_template=self.template_input.isChecked(),
        )

    def _apply(self, dto: TaskEditorDTO):
        self._current_task_id = dto.id
        self.title_input.setText(dto.title)
        self.desc_input.setText(dto.description)
        self.priority_input.setCurrentIndex(max(0, self.priority_input.findData(dto.priority)))
        self.status_input.setCurrentIndex(max(0, self.status_input.findData(dto.status)))
        self.due_input.setDateTime(dto.due_date or datetime.now())
        self.est_cost_input.setText(str(dto.estimated_cost or ""))
        self.actual_cost_input.setText(str(dto.actual_cost or ""))
        self.effort_input.setText(str(dto.effort_hours or ""))
        self.follow_input.setChecked(dto.follow_up_needed)
        self.template_input.setChecked(dto.is_template)

        for list_widget in [self.rooms_selected, self.required_assets, self.materials_list, self.checklist, self.dependencies, self.attachments]:
            list_widget.clear()

        room_names = {room.id: room.name for room in self.task_service.list_rooms()}
        asset_names = {asset.id: asset.name for asset in self.task_service.list_assets()}
        task_names = {task.id: task.title for task in self.task_service.list_tasks()}

        for room_id in dto.room_ids:
            item = QListWidgetItem(room_names.get(room_id, room_id)); item.setData(Qt.UserRole, room_id); self.rooms_selected.addItem(item)
        for asset_id, _, purpose in dto.requires_assets:
            item = QListWidgetItem(self._required_asset_label(asset_names.get(asset_id, asset_id), purpose)); item.setData(Qt.UserRole, (asset_id, purpose)); self.required_assets.addItem(item)
        purchased = set(dto.purchased_material_labels)
        for name, quantity, unit in dto.required_materials:
            data = (name, quantity, unit, name in purchased)
            item = QListWidgetItem(self._material_label(*data)); item.setData(Qt.UserRole, data); self.materials_list.addItem(item)
        for label, done in dto.checklist_items:
            item = QListWidgetItem(f"{'☑' if done else '☐'} {label}"); item.setData(Qt.UserRole, (label, done)); self.checklist.addItem(item)
        for dependency_id in dto.dependency_task_ids:
            item = QListWidgetItem(task_names.get(dependency_id, dependency_id)); item.setData(Qt.UserRole, dependency_id); self.dependencies.addItem(item)
        for path in dto.attachments:
            item = QListWidgetItem(path); item.setData(Qt.UserRole, path); self.attachments.addItem(item)

        for i in range(self.members_list.count()):
            item = self.members_list.item(i)
            item.setSelected(item.data(Qt.UserRole) in set(dto.assigned_member_ids))
        for i in range(self.providers_list.count()):
            item = self.providers_list.item(i)
            item.setSelected(item.data(Qt.UserRole) in set(dto.provider_ids))

        self.recurrence_type.setCurrentIndex(max(0, self.recurrence_type.findData(dto.recurring_type)))
        self.recurrence_interval.setText(str(dto.recurring_interval_days or ""))
        self._dirty = False

    def _decimal_or_none(self, value: str) -> Decimal | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation as exc:
            raise ValueError(f"Invalid decimal: {value}") from exc

    def _save(self):
        try:
            dto = self._collect()
            if not dto.title.strip():
                raise ValueError("Title is required")
            if not dto.room_ids and not dto.requires_assets:
                raise ValueError("Select at least one room or required asset")
            task = self.task_service.save_task_editor_dto(dto)
            self.task_service.session.commit()
            self._current_task_id = task.id
            self._dirty = False
            self.refresh()
            self.data_changed.emit()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Save failed", str(exc))

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
        if QMessageBox.question(self, "Delete task", "Delete current task?") != QMessageBox.Yes:
            return
        try:
            self.task_service.delete_task(self._current_task_id)
            self.task_service.session.commit()
            self._apply(TaskEditorDTO())
            self.refresh()
            self.data_changed.emit()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Delete failed", str(exc))

    def _on_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        task_id = self.model.rows[selected[0].row()].id
        if task_id == self._current_task_id:
            return
        if not self._confirm_navigation_if_dirty():
            return
        self._apply(self.task_service.get_task_editor_dto(task_id))

    def _confirm_navigation_if_dirty(self) -> bool:
        if not self._dirty:
            return True
        return QMessageBox.question(self, "Unsaved changes", "Discard unsaved changes?") == QMessageBox.Yes

    def refresh(self) -> None:
        filters = TaskListFilters(
            statuses=self.status_filter.currentData() or [],
            priorities=self.priority_filter.currentData() or [],
            due_range={"Any": "any", "Overdue": "overdue", "Due today": "today", "Due this week": "week", "Next 7 days": "next7", "Next 30 days": "next30"}[self.due_filter.currentText()],
            room_id=self.room_filter.currentData(),
            asset_id=self.asset_filter.currentData(),
            member_id=self.member_filter.currentData(),
            provider_id=self.provider_filter.currentData(),
            sort_by={"Recently updated": "updated", "Priority": "priority", "Due date": "date", "Room": "room", "Assignee": "assignee"}[self.sort_filter.currentText()],
            search=self.search_input.text(),
        )
        rows = self.task_service.list_task_rows(filters)
        self.model.set_rows(rows)
        self.table.resizeColumnsToContents()
        self._refresh_secondary_views(filters, rows)

    def _refresh_secondary_views(self, filters: TaskListFilters, rows: list[TaskListRow]) -> None:
        self.kanban_list.clear()
        for status, items in self.task_service.list_kanban_rows(filters).items():
            self.kanban_list.addItem(f"=== {status.value} ({len(items)}) ===")
            for row in items:
                self.kanban_list.addItem(f"• {row.title} ({row.priority.value})")

        self.calendar_list.clear()
        dated = sorted([r for r in rows if r.due_date], key=lambda r: r.due_date)
        current_day = None
        for row in dated:
            day = row.due_date.date()
            if day != current_day:
                self.calendar_list.addItem(f"=== {day.isoformat()} ===")
                current_day = day
            self.calendar_list.addItem(f"• {row.title} [{row.status.value}]")

        self.grouped_list.clear()
        self.grouped_list.addItem("=== By room ===")
        for room, items in self.task_service.list_tasks_grouped_by_room(filters).items():
            self.grouped_list.addItem(f"{room}: {len(items)}")
        self.grouped_list.addItem("=== By household member ===")
        for member, items in self.task_service.list_tasks_grouped_by_member(filters).items():
            self.grouped_list.addItem(f"{member}: {len(items)}")
        overdue, today, week = self.task_service.get_due_highlights(filters)
        self.grouped_list.addItem(f"⚠ Overdue: {len(overdue)}")
        self.grouped_list.addItem(f"Today: {len(today)}")
        self.grouped_list.addItem(f"This week: {len(week)}")

    def _duplicate_current(self):
        if not self._current_task_id:
            return
        try:
            task = self.task_service.duplicate_task(self._current_task_id, as_template=False)
            self.task_service.session.commit()
            self._apply(self.task_service.get_task_editor_dto(task.id))
            self.refresh()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Duplicate failed", str(exc))

    def _save_template_copy(self):
        if not self._current_task_id:
            return
        try:
            task = self.task_service.duplicate_task(self._current_task_id, as_template=True)
            self.task_service.session.commit()
            self._apply(self.task_service.get_task_editor_dto(task.id))
            self.refresh()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Template save failed", str(exc))

    def _generate_recurring(self):
        try:
            count = self.task_service.generate_recurring_tasks()
            self.task_service.session.commit()
            self.refresh()
            QMessageBox.information(self, "Recurring tasks", f"Generated {count} recurring task(s).")
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Recurring generation failed", str(exc))
