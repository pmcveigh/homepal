from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class DictListModel(QAbstractListModel):
    """Simple list model backed by a list of dictionaries."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []
        self._role_names: dict[int, bytes] = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def roleNames(self) -> dict[int, bytes]:  # noqa: N802
        return self._role_names

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() < 0 or index.row() >= len(self._rows):
            return None
        if role == Qt.DisplayRole:
            return self._rows[index.row()]
        role_name = self._role_names.get(role)
        if not role_name:
            return None
        key = role_name.decode("utf-8")
        return self._rows[index.row()].get(key)

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        normalized = rows or []
        keys: list[str] = []
        if normalized:
            keys = list(normalized[0].keys())
        self.beginResetModel()
        self._rows = normalized
        self._role_names = {Qt.UserRole + idx + 1: key.encode("utf-8") for idx, key in enumerate(keys)}
        self.endResetModel()

    def get(self, row: int) -> dict[str, Any]:
        if row < 0 or row >= len(self._rows):
            return {}
        return self._rows[row]

    def as_list(self) -> list[dict[str, Any]]:
        return list(self._rows)
