from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from homepal.models import AttributeDefinition
from homepal.services.task_service import TaskService
from homepal.widgets.metadata_factory import build_metadata_widget


@dataclass(slots=True)
class MetadataValidationError:
    messages: list[str]


class MetadataFormWidget(QWidget):
    def __init__(
        self,
        *,
        task_service: TaskService,
        owner_type: str,
        category_id: str | None = None,
        room_type: str | None = None,
        owner_id: str | None = None,
    ):
        super().__init__()
        self.task_service = task_service
        self.owner_type = owner_type
        self.category_id = category_id
        self.room_type = room_type
        self.owner_id = owner_id

        self.layout = QFormLayout(self)
        self._definitions: list[AttributeDefinition] = []
        self._fields: dict[str, QWidget] = {}

        self.rebuild(category_id=category_id, room_type=room_type, owner_id=owner_id)

    @property
    def definition_ids(self) -> list[str]:
        return [item.id for item in self._definitions]

    def rebuild(self, *, category_id: str | None = None, room_type: str | None = None, owner_id: str | None = None) -> None:
        self.category_id = category_id
        self.room_type = room_type
        self.owner_id = owner_id

        while self.layout.rowCount() > 0:
            self.layout.removeRow(0)

        self._fields.clear()
        self._definitions = self.task_service.list_attribute_definitions(
            applies_to=self.owner_type,
            category_id=self.category_id,
            room_type=self.room_type,
        )

        existing_values = self.task_service.get_attribute_values(
            owner_type=self.owner_type,
            owner_id=self.owner_id,
        ) if self.owner_id else {}

        for definition in self._definitions:
            label_text = definition.display_name
            if definition.unit:
                label_text = f"{label_text} ({definition.unit})"
            if definition.required:
                label_text = f"{label_text} *"

            field = build_metadata_widget(definition)
            if definition.id in existing_values:
                field.set_value(existing_values[definition.id])
            self._fields[definition.id] = field
            self.layout.addRow(QLabel(label_text), field)

    def validate(self) -> MetadataValidationError | None:
        messages: list[str] = []
        for definition in self._definitions:
            if definition.required and self._fields[definition.id].get_value() in (None, ""):
                messages.append(definition.display_name)
        if messages:
            return MetadataValidationError(messages)
        return None

    def collect_values(self) -> dict[str, object]:
        return {definition.id: self._fields[definition.id].get_value() for definition in self._definitions}

    def persist_values(self, owner_id: str) -> None:
        values = self.collect_values()
        self.task_service.upsert_attribute_values(
            owner_type=self.owner_type,
            owner_id=owner_id,
            values=values,
            active_definition_ids=self.definition_ids,
            definitions=self._definitions,
        )
