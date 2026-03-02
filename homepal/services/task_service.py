from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from getpass import getuser

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from homepal.models import (
    ALLOWED_TRANSITIONS,
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

    def create_task(
        self,
        *,
        title: str,
        description: str,
        priority: Priority = Priority.P3,
        due_date: date | None = None,
    ) -> Task:
        room = self.ensure_default_room()
        task = Task(
            title=title.strip(),
            description=description.strip() or "No description provided",
            priority=priority,
            status=TaskStatus.OPEN,
            room_id=room.id,
            due_date=due_date,
        )
        self.session.add(task)
        self.session.flush()
        self._history(task.id, "status", None, TaskStatus.OPEN.value)
        return task

    def list_tasks(self) -> list[Task]:
        return list(self.session.scalars(select(Task).order_by(Task.created_at.desc())))

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

        return DashboardStats(
            open_tasks=open_tasks,
            overdue_tasks=overdue_tasks,
            p1_tasks=p1_tasks,
            due_this_week=due_this_week,
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
