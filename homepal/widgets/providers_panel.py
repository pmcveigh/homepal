from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from homepal.models import ServiceProvider
from homepal.services.provider_service import ProviderSaveDTO, ProviderService
from homepal.services.task_service import ProviderListRow, TaskService


SERVICE_TYPES = [
    "Energy (Electricity)",
    "Energy (Gas)",
    "Water",
    "Broadband",
    "Mobile",
    "TV Licence",
    "Council Tax",
    "Home Insurance",
    "Boiler Cover",
    "Security Monitoring",
    "Other",
]


class ProviderTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.headers = ["Provider", "Service", "Account no.", "Phone", "Monthly cost", "Contract end"]
        self.rows: list[ProviderListRow] = []

    def set_rows(self, rows: list[ProviderListRow]) -> None:
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        provider = self.rows[index.row()]
        values = [
            provider.name,
            provider.service_type,
            provider.account_number or "-",
            provider.phone_number or "-",
            f"£{provider.monthly_cost_estimate:.2f}" if provider.monthly_cost_estimate is not None else "-",
            provider.contract_end_date.isoformat() if provider.contract_end_date else "-",
        ]
        return values[index.column()]


class ProvidersPanel(QWidget):
    def __init__(self, task_service: TaskService, on_data_changed):
        super().__init__()
        self.task_service = task_service
        self.provider_service = ProviderService(task_service)
        self.on_data_changed = on_data_changed
        self.current_provider_id: str | None = None
        self._provider_rows: list[ProviderListRow] = []

        root = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        self.add_btn = QPushButton("Add provider")
        self.delete_btn = QPushButton("Delete provider")
        self.delete_btn.setEnabled(False)
        self.search = QLineEdit(); self.search.setPlaceholderText("Search by provider, account no. or phone")
        self.service_type = QComboBox(); self.service_type.addItem("All services")
        for service_type in SERVICE_TYPES:
            self.service_type.addItem(service_type)

        for widget in [self.add_btn, self.delete_btn, self.search, self.service_type]:
            toolbar.addWidget(widget)
        root.addLayout(toolbar)

        self.table_model = ProviderTableModel()
        self.table = QTableView(); self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        root.addWidget(self.table)

        form = QFormLayout()
        self.name = QLineEdit()
        self.service_type_edit = QComboBox(); self.service_type_edit.addItems(SERVICE_TYPES)
        self.account_number = QLineEdit()
        self.phone_number = QLineEdit()
        self.website = QLineEdit()
        self.monthly_cost = QLineEdit(); self.monthly_cost.setPlaceholderText("e.g. 89.50")
        self.contract_end = QDateEdit(); self.contract_end.setCalendarPopup(True); self.contract_end.setDisplayFormat("dd/MM/yyyy")
        self.contract_end.setDate(QDate.currentDate()); self.contract_end.setSpecialValueText("No contract end date")
        self.contract_end.setMinimumDate(QDate(1900, 1, 1)); self.contract_end.setDate(self.contract_end.minimumDate())
        self.notes = QTextEdit()
        self.save_btn = QPushButton("Save provider")

        form.addRow("Provider name", self.name)
        form.addRow("Service type", self.service_type_edit)
        form.addRow("Account number", self.account_number)
        form.addRow("Phone number", self.phone_number)
        form.addRow("Website", self.website)
        form.addRow("Estimated monthly cost (£)", self.monthly_cost)
        form.addRow("Contract end date", self.contract_end)
        form.addRow("Notes", self.notes)
        form.addRow("", self.save_btn)
        root.addLayout(form)

        self.add_btn.clicked.connect(self._new_provider)
        self.delete_btn.clicked.connect(self._delete_provider)
        self.save_btn.clicked.connect(self._save_provider)
        self.search.textChanged.connect(self.refresh)
        self.service_type.currentIndexChanged.connect(self.refresh)
        self.table.selectionModel().selectionChanged.connect(self._provider_selected)

        self.refresh()

    def _selected_service_type(self) -> str:
        return "all" if self.service_type.currentIndex() == 0 else self.service_type.currentText()

    def refresh(self) -> None:
        self._provider_rows = self.provider_service.list_providers(
            service_type=self._selected_service_type(),
            search=self.search.text(),
        )
        self.table_model.set_rows(self._provider_rows)
        self.table.resizeColumnsToContents()

        if self.current_provider_id and not any(p.id == self.current_provider_id for p in self._provider_rows):
            self.current_provider_id = None
            self.delete_btn.setEnabled(False)

    def _provider_selected(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        provider = self._provider_rows[selected[0].row()]
        self.current_provider_id = provider.id
        self.delete_btn.setEnabled(True)

        stored = self.task_service.session.get(ServiceProvider, provider.id)
        if stored is None:
            return
        self.name.setText(stored.name)
        self.service_type_edit.setCurrentText(stored.service_type)
        self.account_number.setText(stored.account_number or "")
        self.phone_number.setText(stored.phone_number or "")
        self.website.setText(stored.website or "")
        self.monthly_cost.setText(f"{stored.monthly_cost_estimate:.2f}" if stored.monthly_cost_estimate is not None else "")
        self.notes.setPlainText(stored.notes or "")
        if stored.contract_end_date:
            self.contract_end.setDate(QDate(stored.contract_end_date.year, stored.contract_end_date.month, stored.contract_end_date.day))
        else:
            self.contract_end.setDate(self.contract_end.minimumDate())

    def _new_provider(self) -> None:
        self.current_provider_id = None
        self.table.clearSelection()
        self.delete_btn.setEnabled(False)
        self.name.clear()
        self.service_type_edit.setCurrentIndex(0)
        self.account_number.clear()
        self.phone_number.clear()
        self.website.clear()
        self.monthly_cost.clear()
        self.notes.clear()
        self.contract_end.setDate(self.contract_end.minimumDate())

    def _save_provider(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(self, "Validation", "Provider name is required")
            return

        monthly_cost_estimate = None
        if self.monthly_cost.text().strip():
            try:
                monthly_cost_estimate = Decimal(self.monthly_cost.text().strip())
            except InvalidOperation:
                QMessageBox.warning(self, "Validation", "Estimated monthly cost must be a valid number")
                return

        contract_end_date = None
        if self.contract_end.date() != self.contract_end.minimumDate():
            qdate = self.contract_end.date()
            contract_end_date = qdate.toPython()

        dto = ProviderSaveDTO(
            id=self.current_provider_id,
            name=self.name.text(),
            service_type=self.service_type_edit.currentText(),
            account_number=self.account_number.text(),
            phone_number=self.phone_number.text(),
            website=self.website.text(),
            monthly_cost_estimate=monthly_cost_estimate,
            contract_end_date=contract_end_date,
            notes=self.notes.toPlainText(),
        )

        try:
            provider = self.provider_service.save_provider(dto)
            self.task_service.session.commit()
            self.refresh()
            self._select_provider(provider.id)
            self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Save failed", str(exc))

    def _select_provider(self, provider_id: str) -> None:
        for idx, row in enumerate(self._provider_rows):
            if row.id == provider_id:
                self.table.selectRow(idx)
                self._provider_selected()
                return

    def _delete_provider(self) -> None:
        if not self.current_provider_id:
            QMessageBox.information(self, "Delete provider", "Select a provider to delete")
            return

        selected = self.table.selectionModel().selectedRows()
        provider_name = self._provider_rows[selected[0].row()].name if selected else "this provider"
        answer = QMessageBox.question(
            self,
            "Delete provider",
            f"Delete provider '{provider_name}'? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return

        try:
            self.provider_service.delete_provider(self.current_provider_id)
            self.task_service.session.commit()
            self._new_provider()
            self.refresh()
            self.on_data_changed()
        except Exception as exc:
            self.task_service.session.rollback()
            QMessageBox.warning(self, "Delete failed", str(exc))
