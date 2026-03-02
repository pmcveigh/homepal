from __future__ import annotations

from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from homepal.models import ValueType
from homepal.utils.labels import humanise_token


class MetadataField(QWidget):
    def get_value(self):
        raise NotImplementedError

    def set_value(self, value) -> None:
        raise NotImplementedError


class TextField(MetadataField):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.input = QLineEdit()
        layout.addWidget(self.input)

    def get_value(self):
        value = self.input.text().strip()
        return value or None

    def set_value(self, value) -> None:
        self.input.setText(value or "")


class BoolField(MetadataField):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.input = QCheckBox()
        layout.addWidget(self.input)

    def get_value(self):
        return self.input.isChecked()

    def set_value(self, value) -> None:
        self.input.setChecked(bool(value))


class NullableSpinField(MetadataField):
    def __init__(self, *, decimal: bool):
        super().__init__()
        self.decimal = decimal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.has_value = QCheckBox("Has value")
        self.has_value.setChecked(False)
        self.has_value.toggled.connect(self._on_toggle)
        layout.addWidget(self.has_value)

        if decimal:
            self.input = QDoubleSpinBox()
            self.input.setDecimals(3)
            self.input.setRange(0, 10_000_000)
        else:
            self.input = QSpinBox()
            self.input.setRange(-1_000_000, 1_000_000)
        self.input.setEnabled(False)
        layout.addWidget(self.input)

    def _on_toggle(self, checked: bool) -> None:
        self.input.setEnabled(checked)

    def get_value(self):
        if not self.has_value.isChecked():
            return None
        return self.input.value()

    def set_value(self, value) -> None:
        has = value is not None
        self.has_value.setChecked(has)
        self.input.setEnabled(has)
        if has:
            self.input.setValue(float(value) if self.decimal else int(value))


class NullableDateField(MetadataField):
    def __init__(self):
        super().__init__()
        self._is_null = True
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setEnabled(False)
        layout.addWidget(self.date_edit)

        self.set_btn = QPushButton("Set")
        self.set_btn.clicked.connect(self._enable)
        layout.addWidget(self.set_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear)
        layout.addWidget(self.clear_btn)

    def _enable(self) -> None:
        self._is_null = False
        self.date_edit.setEnabled(True)

    def _clear(self) -> None:
        self._is_null = True
        self.date_edit.setEnabled(False)

    def get_value(self):
        if self._is_null:
            return None
        return self.date_edit.date().toPython()

    def set_value(self, value) -> None:
        if not value:
            self._clear()
            return
        self._enable()
        if isinstance(value, date):
            self.date_edit.setDate(QDate(value.year, value.month, value.day))


class ChoiceField(MetadataField):
    def __init__(self, choices: list[str]):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.addItem("-- Select --", None)
        for token in choices:
            self.combo.addItem(humanise_token(token), token)
        layout.addWidget(self.combo)

    def get_value(self):
        return self.combo.currentData()

    def set_value(self, value) -> None:
        idx = self.combo.findData(value)
        self.combo.setCurrentIndex(max(idx, 0))


def build_metadata_widget(definition) -> MetadataField:
    value_type = definition.value_type
    if value_type == ValueType.TEXT:
        return TextField()
    if value_type == ValueType.INT:
        return NullableSpinField(decimal=False)
    if value_type == ValueType.DECIMAL:
        return NullableSpinField(decimal=True)
    if value_type == ValueType.BOOL:
        return BoolField()
    if value_type == ValueType.DATE:
        return NullableDateField()
    if value_type == ValueType.CHOICE:
        choices = [item.strip() for item in (definition.choices_csv or "").split(",") if item.strip()]
        return ChoiceField(choices)
    return TextField()
