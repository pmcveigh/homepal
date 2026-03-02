from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from getpass import getuser

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from homepal.models import (
    ALLOWED_TRANSITIONS,
    Asset,
    AssetCategory,
    AssetRoomLink,
    AttributeDefinition,
    AttributeValue,
    LinkRole,
    Priority,
    Property,
    Room,
    Task,
    TaskAssetLink,
    TaskHistory,
    TaskRoomLink,
    TaskStatus,
    ValueType,
    compute_next_due_date,
)


@dataclass(slots=True)
class DashboardStats:
    open_tasks: int
    overdue_tasks: int
    p1_tasks: int
    due_this_week: int
    total_rooms: int
    total_assets: int


@dataclass(slots=True)
class ReportSummary:
    total_tasks: int
    completed_tasks: int
    open_tasks: int
    overdue_tasks: int
    urgent_tasks: int
    estimated_cost_total: Decimal
    actual_cost_total: Decimal


class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def transition_status(self, task: Task, new_status: TaskStatus) -> None:
        allowed = ALLOWED_TRANSITIONS[task.status]
        if new_status not in allowed:
            raise ValueError(f"Invalid transition {task.status.value} -> {new_status.value}")
        old = task.status
        task.status = new_status
        self.session.flush()
        self._history(task.id, "status", old.value, new_status.value)
        if new_status == TaskStatus.COMPLETED and task.recurring_schedule:
            self._create_next_recurring_instance(task)

    def ensure_default_room(self) -> Room:
        room = self.session.scalar(select(Room).where(Room.name == "General"))
        if room:
            return room

        prop = self.session.scalar(select(Property).where(Property.name == "Home"))
        if prop is None:
            prop = Property(name="Home", address="")
            self.session.add(prop)
            self.session.flush()

        room = Room(property_id=prop.id, name="General", description="Default room for uncategorized tasks")
        self.session.add(room)
        self.session.flush()
        return room

    def create_room(self, *, name: str, description: str = "", floor_level: str = "") -> Room:
        prop = self.session.scalar(select(Property).where(Property.name == "Home"))
        if prop is None:
            prop = Property(name="Home", address="")
            self.session.add(prop)
            self.session.flush()

        room = Room(
            property_id=prop.id,
            name=name.strip(),
            description=description.strip() or None,
            floor_level=floor_level.strip() or None,
        )
        self.session.add(room)
        self.session.flush()
        return room

    def list_rooms(self) -> list[Room]:
        return list(self.session.scalars(select(Room).order_by(Room.name.asc())))


    def list_asset_categories(self) -> list[AssetCategory]:
        return list(
            self.session.scalars(
                select(AssetCategory).where(AssetCategory.is_active.is_(True)).order_by(AssetCategory.display_name.asc())
            )
        )

    def get_or_create_asset_category(self, code: str, display_name: str | None = None) -> AssetCategory:
        normalized = code.strip().lower()
        if not normalized:
            raise ValueError("Asset category code is required")

        category = self.session.scalar(select(AssetCategory).where(AssetCategory.code == normalized))
        if category:
            return category

        category = AssetCategory(code=normalized, display_name=(display_name or code).strip(), is_active=True)
        self.session.add(category)
        self.session.flush()
        return category

    def create_asset(
        self,
        *,
        primary_room_id: str | None = None,
        room_id: str | None = None,
        name: str = "",
        category_code: str | None = None,
        category: str | None = None,
        also_used_in_room_ids: list[str] | None = None,
        notes: str = "",
        is_fixed: bool = False,
        vendor: str | None = None,
    ) -> Asset:
        resolved_primary_room = primary_room_id or room_id
        if not resolved_primary_room:
            raise ValueError("primary_room_id is required")

        resolved_category_code = (category_code or category or "general").strip().lower().replace(" ", "_")
        category = self.get_or_create_asset_category(
            resolved_category_code,
            display_name=(category_code or category or "General").replace("_", " ").title(),
        )

        asset = Asset(
            room_id=resolved_primary_room,
            name=name.strip(),
            category=category.display_name,
            category_id=category.id,
            notes=notes.strip() or None,
        )
        self.session.add(asset)
        self.session.flush()

        room_ids = [resolved_primary_room]
        for room_id in also_used_in_room_ids or []:
            if room_id not in room_ids:
                room_ids.append(room_id)

        self.set_asset_room_links(asset.id, primary_room_id=resolved_primary_room, room_ids=room_ids)
        return asset

    def set_asset_room_links(self, asset_id: str, *, primary_room_id: str, room_ids: list[str]) -> None:
        if primary_room_id not in room_ids:
            raise ValueError("Primary room must be included in room_ids")

        self.session.query(AssetRoomLink).where(AssetRoomLink.asset_id == asset_id).delete(synchronize_session=False)
        for room_id in room_ids:
            self.session.add(
                AssetRoomLink(
                    asset_id=asset_id,
                    room_id=room_id,
                    is_primary=(room_id == primary_room_id),
                )
            )

        self.session.flush()

    def list_assets(self) -> list[Asset]:
        return list(self.session.scalars(select(Asset).order_by(Asset.name.asc())))

    def create_task(
        self,
        *,
        title: str,
        description: str,
        priority: Priority = Priority.P3,
        due_date: date | None = None,
        is_urgent: bool = False,
        requires_follow_up: bool = False,
        estimated_effort_hours: Decimal | None = None,
        labels: str | None = None,
        room_ids: list[str] | None = None,
        about_asset_ids: list[str] | None = None,
        uses_asset_ids: list[str] | None = None,
        requires_assets: list[tuple[str, Decimal | None, str | None]] | None = None,
    ) -> Task:
        fallback_room = self.ensure_default_room()
        normalized_room_ids = list(dict.fromkeys(room_ids or [fallback_room.id]))
        normalized_about = list(dict.fromkeys(about_asset_ids or []))
        normalized_uses = list(dict.fromkeys(uses_asset_ids or []))
        normalized_requires = requires_assets or []

        if not normalized_room_ids and not normalized_about:
            raise ValueError("Task must have at least one room or one ABOUT asset")

        task = Task(
            title=title.strip(),
            description=description.strip() or "No description provided",
            priority=priority,
            status=TaskStatus.OPEN,
            room_id=normalized_room_ids[0] if normalized_room_ids else None,
            asset_id=normalized_about[0] if normalized_about else None,
            due_date=due_date,
            is_urgent=is_urgent,
            requires_follow_up=requires_follow_up,
            estimated_effort_hours=estimated_effort_hours,
            labels=labels.strip() if labels else None,
        )
        self.session.add(task)
        self.session.flush()

        self._set_task_room_links(task.id, normalized_room_ids)
        self._set_task_asset_links(task.id, normalized_about, normalized_uses, normalized_requires)

        self._history(task.id, "status", None, TaskStatus.OPEN.value)
        return task

    def _set_task_room_links(self, task_id: str, room_ids: list[str]) -> None:
        self.session.query(TaskRoomLink).where(TaskRoomLink.task_id == task_id).delete(synchronize_session=False)
        for room_id in room_ids:
            self.session.add(TaskRoomLink(task_id=task_id, room_id=room_id))
        self.session.flush()

    def _set_task_asset_links(
        self,
        task_id: str,
        about_asset_ids: list[str],
        uses_asset_ids: list[str],
        requires_assets: list[tuple[str, Decimal | None, str | None]],
    ) -> None:
        self.session.query(TaskAssetLink).where(TaskAssetLink.task_id == task_id).delete(synchronize_session=False)
        for asset_id in about_asset_ids:
            self.session.add(TaskAssetLink(task_id=task_id, asset_id=asset_id, role=LinkRole.ABOUT))
        for asset_id in uses_asset_ids:
            self.session.add(TaskAssetLink(task_id=task_id, asset_id=asset_id, role=LinkRole.USES))
        for asset_id, quantity, unit in requires_assets:
            self.session.add(
                TaskAssetLink(
                    task_id=task_id,
                    asset_id=asset_id,
                    role=LinkRole.REQUIRES,
                    quantity=quantity,
                    unit=unit,
                )
            )
        self.session.flush()

    def list_tasks(self) -> list[Task]:
        return list(self.session.scalars(select(Task).order_by(Task.created_at.desc())))

    def list_calendar_tasks(self, month: int, year: int) -> list[Task]:
        month_start = date(year, month, 1)
        month_end = date(year + (month // 12), (month % 12) + 1, 1)
        return list(
            self.session.scalars(
                select(Task)
                .where(Task.due_date.is_not(None), Task.due_date >= month_start, Task.due_date < month_end)
                .order_by(Task.due_date.asc())
            )
        )

    def get_dashboard_stats(self, today: date | None = None) -> DashboardStats:
        today = today or date.today()
        week_end = today + timedelta(days=7)

        open_tasks = self.session.scalar(
            select(func.count(Task.id)).where(Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]))
        ) or 0
        overdue_tasks = self.session.scalar(
            select(func.count(Task.id)).where(
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        ) or 0
        p1_tasks = self.session.scalar(
            select(func.count(Task.id)).where(Task.priority == Priority.P1, Task.status != TaskStatus.ARCHIVED)
        ) or 0
        due_this_week = self.session.scalar(
            select(func.count(Task.id)).where(
                Task.due_date.is_not(None),
                Task.due_date >= today,
                Task.due_date <= week_end,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        ) or 0
        total_rooms = self.session.scalar(select(func.count(Room.id))) or 0
        total_assets = self.session.scalar(select(func.count(Asset.id))) or 0

        return DashboardStats(
            open_tasks=open_tasks,
            overdue_tasks=overdue_tasks,
            p1_tasks=p1_tasks,
            due_this_week=due_this_week,
            total_rooms=total_rooms,
            total_assets=total_assets,
        )

    def generate_report_summary(self, today: date | None = None) -> ReportSummary:
        today = today or date.today()
        total_tasks = self.session.scalar(select(func.count(Task.id))) or 0
        completed_tasks = self.session.scalar(select(func.count(Task.id)).where(Task.status == TaskStatus.COMPLETED)) or 0
        open_tasks = self.session.scalar(
            select(func.count(Task.id)).where(Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]))
        ) or 0
        overdue_tasks = self.session.scalar(
            select(func.count(Task.id)).where(
                Task.due_date.is_not(None),
                Task.due_date < today,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
        ) or 0
        urgent_tasks = self.session.scalar(
            select(func.count(Task.id)).where(Task.is_urgent.is_(True), Task.status != TaskStatus.ARCHIVED)
        ) or 0
        estimated_cost_total = self.session.scalar(select(func.coalesce(func.sum(Task.estimated_cost), 0))) or 0
        actual_cost_total = self.session.scalar(select(func.coalesce(func.sum(Task.actual_cost), 0))) or 0

        return ReportSummary(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            open_tasks=open_tasks,
            overdue_tasks=overdue_tasks,
            urgent_tasks=urgent_tasks,
            estimated_cost_total=Decimal(str(estimated_cost_total)),
            actual_cost_total=Decimal(str(actual_cost_total)),
        )

    def list_tasks_by_asset_role(self, role: LinkRole) -> list[Task]:
        return list(
            self.session.scalars(
                select(Task)
                .join(TaskAssetLink, TaskAssetLink.task_id == Task.id)
                .where(TaskAssetLink.role == role)
                .order_by(Task.created_at.desc())
            )
        )

    def list_assets_in_room(self, room_id: str) -> list[Asset]:
        return list(
            self.session.scalars(
                select(Asset)
                .join(AssetRoomLink, AssetRoomLink.asset_id == Asset.id)
                .where(AssetRoomLink.room_id == room_id)
                .order_by(Asset.name.asc())
            )
        )

    def list_attribute_definitions(
        self,
        *,
        applies_to: str,
        category_id: str | None = None,
        room_type: str | None = None,
    ) -> list[AttributeDefinition]:
        query = select(AttributeDefinition).where(AttributeDefinition.applies_to == applies_to)
        if applies_to == "asset":
            query = query.where(or_(AttributeDefinition.category_id == category_id, AttributeDefinition.category_id.is_(None)))
        if applies_to == "room":
            query = query.where(
                or_(
                    AttributeDefinition.room_type == room_type,
                    AttributeDefinition.room_type == "any",
                    AttributeDefinition.room_type.is_(None),
                )
            )

        definitions = list(self.session.scalars(query))

        def scope_rank(item: AttributeDefinition) -> tuple[int, str]:
            if applies_to == "asset":
                return (0 if item.category_id == category_id and category_id else 1, item.display_name.lower())
            if applies_to == "room":
                if item.room_type == room_type and room_type not in (None, "any"):
                    return (0, item.display_name.lower())
                if item.room_type == "any":
                    return (1, item.display_name.lower())
                return (2, item.display_name.lower())
            return (0, item.display_name.lower())

        return sorted(definitions, key=scope_rank)

    def get_attribute_values(self, *, owner_type: str, owner_id: str | None) -> dict[str, object]:
        if not owner_id:
            return {}

        query = select(AttributeValue).where(
            AttributeValue.asset_id == owner_id if owner_type == "asset" else AttributeValue.room_id == owner_id
        )
        values: dict[str, object] = {}
        for row in self.session.scalars(query):
            if row.value_text is not None:
                values[row.definition_id] = row.value_text
            elif row.value_int is not None:
                values[row.definition_id] = row.value_int
            elif row.value_decimal is not None:
                values[row.definition_id] = float(row.value_decimal)
            elif row.value_bool is not None:
                values[row.definition_id] = row.value_bool
            elif row.value_date is not None:
                values[row.definition_id] = row.value_date
            else:
                values[row.definition_id] = None
        return values

    def upsert_attribute_values(
        self,
        *,
        owner_type: str,
        owner_id: str,
        values: dict[str, object],
        active_definition_ids: list[str],
        definitions: list[AttributeDefinition],
    ) -> None:
        target_filter = AttributeValue.asset_id == owner_id if owner_type == "asset" else AttributeValue.room_id == owner_id
        existing = {row.definition_id: row for row in self.session.scalars(select(AttributeValue).where(target_filter))}
        definition_map = {item.id: item for item in definitions}

        stale_ids = [item_id for item_id in existing if item_id not in active_definition_ids]
        if stale_ids:
            self.session.query(AttributeValue).where(target_filter, AttributeValue.definition_id.in_(stale_ids)).delete(synchronize_session=False)

        for definition_id, value in values.items():
            definition = definition_map[definition_id]
            row = existing.get(definition_id)
            if row is None:
                row = AttributeValue(definition_id=definition_id, asset_id=owner_id if owner_type == "asset" else None, room_id=owner_id if owner_type == "room" else None)
                self.session.add(row)

            row.value_text = None
            row.value_int = None
            row.value_decimal = None
            row.value_bool = None
            row.value_date = None

            if value is None:
                continue
            if definition.value_type in {ValueType.TEXT, ValueType.CHOICE}:
                row.value_text = str(value)
            elif definition.value_type == ValueType.INT:
                row.value_int = int(value)
            elif definition.value_type == ValueType.DECIMAL:
                row.value_decimal = Decimal(str(value))
            elif definition.value_type == ValueType.BOOL:
                row.value_bool = bool(value)
            elif definition.value_type == ValueType.DATE:
                row.value_date = value

        self.session.flush()

    def _create_next_recurring_instance(self, completed_task: Task) -> None:
        next_due = compute_next_due_date(completed_task.recurring_schedule, date.today())
        cloned = Task(
            title=completed_task.title,
            description=completed_task.description,
            priority=completed_task.priority,
            status=TaskStatus.OPEN,
            room_id=completed_task.room_id,
            asset_id=completed_task.asset_id,
            recurring_schedule_id=completed_task.recurring_schedule_id,
            parent_task_id=completed_task.id,
            due_date=next_due,
            estimated_cost=completed_task.estimated_cost,
            notes=completed_task.notes,
            is_urgent=completed_task.is_urgent,
            requires_follow_up=completed_task.requires_follow_up,
            estimated_effort_hours=completed_task.estimated_effort_hours,
            labels=completed_task.labels,
        )
        self.session.add(cloned)

    def _history(self, task_id: str, field: str, old: str | None, new: str | None) -> None:
        if not task_id:
            return
        self.session.add(
            TaskHistory(
                task_id=task_id,
                field_changed=field,
                old_value=old,
                new_value=new,
                user_identifier=getuser(),
            )
        )
