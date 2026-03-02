from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from getpass import getuser

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from homepal.models import (
    ALLOWED_TRANSITIONS,
    Asset,
    Priority,
    Property,
    Room,
    Task,
    TaskHistory,
    TaskStatus,
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

    def create_asset(
        self,
        *,
        room_id: str,
        name: str,
        category: str,
        notes: str = "",
    ) -> Asset:
        asset = Asset(
            room_id=room_id,
            name=name.strip(),
            category=category.strip() or "General",
            notes=notes.strip() or None,
        )
        self.session.add(asset)
        self.session.flush()
        return asset

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
    ) -> Task:
        room = self.ensure_default_room()
        task = Task(
            title=title.strip(),
            description=description.strip() or "No description provided",
            priority=priority,
            status=TaskStatus.OPEN,
            room_id=room.id,
            due_date=due_date,
            is_urgent=is_urgent,
            requires_follow_up=requires_follow_up,
            estimated_effort_hours=estimated_effort_hours,
            labels=labels.strip() if labels else None,
        )
        self.session.add(task)
        self.session.flush()
        self._history(task.id, "status", None, TaskStatus.OPEN.value)
        return task

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
        self.session.add(
            TaskHistory(
                task_id=task_id,
                field_changed=field,
                old_value=old,
                new_value=new,
                user_identifier=getuser(),
            )
        )
