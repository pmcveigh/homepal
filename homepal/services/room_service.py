from __future__ import annotations

from dataclasses import dataclass

from homepal.models import Room
from homepal.services.task_service import TaskService


@dataclass(slots=True)
class RoomSaveDTO:
    id: str | None = None
    name: str = ""
    room_type: str = "any"
    floor_level: str = ""
    notes: str = ""


class RoomService:
    def __init__(self, task_service: TaskService):
        self.task_service = task_service

    def list_rooms_overview(self, *, search: str = "", room_type: str = "any"):
        return self.task_service.list_rooms_overview(search=search, room_type=room_type)

    def save_room(self, dto: RoomSaveDTO) -> Room:
        session = self.task_service.session
        if dto.id:
            room = session.get(Room, dto.id)
            if room is None:
                raise ValueError("Room not found")
            room.name = dto.name.strip()
            room.description = dto.room_type
            room.floor_level = dto.floor_level.strip() or None
            room.notes = dto.notes.strip() or None
            session.flush()
            return room

        return self.task_service.create_room(name=dto.name, description=dto.room_type, floor_level=dto.floor_level)
    def delete_room(self, room_id: str) -> None:
        self.task_service.delete_room(room_id)

