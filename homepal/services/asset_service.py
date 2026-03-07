from __future__ import annotations

from dataclasses import dataclass, field

from homepal.models import Asset
from homepal.services.task_service import TaskService


@dataclass(slots=True)
class AssetSaveDTO:
    id: str | None = None
    name: str = ""
    category: str = "General"
    primary_room_id: str | None = None
    used_room_ids: list[str] = field(default_factory=list)
    notes: str = ""


class AssetService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    def list_assets_for_room(self, room_id: str, *, category: str = "any", warranty_soon: bool = False, portable_only: bool = False):
        return self.task_service.list_assets_for_room(
            room_id,
            category=category,
            warranty_soon=warranty_soon,
            portable_only=portable_only,
        )

    def list_asset_room_ids(self, asset_id: str) -> list[str]:
        return self.task_service.list_asset_room_ids(asset_id)

    def delete_asset(self, asset_id: str) -> None:
        self.task_service.delete_asset(asset_id)

    def save_asset(self, dto: AssetSaveDTO) -> Asset:
        session = self.task_service.session
        if dto.id:
            asset = session.get(Asset, dto.id)
            if asset is None:
                raise ValueError("Asset not found")
            asset.name = dto.name.strip()
            asset.category = dto.category
            asset.notes = dto.notes.strip() or None
            if dto.primary_room_id:
                asset.room_id = dto.primary_room_id
                room_ids = list(dict.fromkeys([dto.primary_room_id, *dto.used_room_ids]))
                self.task_service.set_asset_room_links(asset.id, primary_room_id=dto.primary_room_id, room_ids=room_ids)
            session.flush()
            return asset

        if not dto.primary_room_id:
            raise ValueError("Primary room is required")
        return self.task_service.create_asset(
            primary_room_id=dto.primary_room_id,
            also_used_in_room_ids=dto.used_room_ids,
            name=dto.name,
            category=dto.category,
            notes=dto.notes,
        )
