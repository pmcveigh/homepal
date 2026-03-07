from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import Priority, RecurrenceType, RecurringSchedule, Task, TaskStatus
from homepal.services.task_service import TaskService


@pytest.fixture()
def session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def test_invalid_transition_raises(session):
    task = Task(title="T", description="D", priority=Priority.P3, status=TaskStatus.DRAFT, room_id="room")
    session.add(task)
    session.commit()

    svc = TaskService(session)
    with pytest.raises(ValueError):
        svc.transition_status(task, TaskStatus.COMPLETED)


def test_completion_creates_next_recurring_task(session):
    schedule = RecurringSchedule(
        recurrence_type=RecurrenceType.AFTER_COMPLETION_N_DAYS,
        completion_offset=30,
    )
    task = Task(
        title="Change filter",
        description="HVAC filter",
        priority=Priority.P2,
        status=TaskStatus.IN_PROGRESS,
        room_id="room",
        recurring_schedule=schedule,
        is_urgent=True,
    )
    session.add_all([schedule, task])

    svc = TaskService(session)
    svc.transition_status(task, TaskStatus.COMPLETED)
    session.commit()

    tasks = session.query(Task).all()
    assert len(tasks) == 2
    new_task = next(t for t in tasks if t.id != task.id)
    assert new_task.status == TaskStatus.OPEN
    assert new_task.parent_task_id == task.id
    assert new_task.due_date == datetime.combine(date.today() + timedelta(days=30), time.min)
    assert new_task.is_urgent is True


def test_dashboard_stats_counts(session):
    today = date(2026, 1, 10)
    session.add_all(
        [
            Task(title="Open overdue", description="d", priority=Priority.P1, status=TaskStatus.OPEN, room_id="r", due_date=datetime.combine(today - timedelta(days=1), time.min)),
            Task(title="In progress", description="d", priority=Priority.P2, status=TaskStatus.IN_PROGRESS, room_id="r", due_date=datetime.combine(today + timedelta(days=2), time.min)),
            Task(title="Archived", description="d", priority=Priority.P1, status=TaskStatus.ARCHIVED, room_id="r"),
        ]
    )
    session.commit()

    svc = TaskService(session)
    stats = svc.get_dashboard_stats(today=today)

    assert stats.open_tasks == 2
    assert stats.overdue_tasks == 1
    assert stats.p1_tasks == 1
    assert stats.due_this_week == 1


def test_create_task_uses_default_room(session):
    svc = TaskService(session)
    created = svc.create_task(
        title="Replace bulbs",
        description="Hallway lights",
        is_urgent=True,
        requires_follow_up=True,
        estimated_effort_hours=Decimal("1.5"),
        labels="lighting,quick",
    )
    session.commit()

    stored = session.get(Task, created.id)
    assert stored is not None
    assert stored.room_id is not None
    assert stored.status == TaskStatus.OPEN
    assert stored.is_urgent is True
    assert stored.requires_follow_up is True
    assert stored.estimated_effort_hours == Decimal("1.5")
    assert stored.labels == "lighting,quick"


def test_room_asset_report_and_calendar(session):
    svc = TaskService(session)
    room = svc.create_room(name="Kitchen", floor_level="1")
    svc.create_asset(room_id=room.id, name="Dishwasher", category="Appliance")
    svc.create_task(title="Inspect dishwasher", description="Check seals", due_date=datetime(2026, 1, 5, 9, 30), is_urgent=True)
    session.commit()

    report = svc.generate_report_summary(today=date(2026, 1, 10))
    january_tasks = svc.list_calendar_tasks(month=1, year=2026)

    assert report.total_tasks == 1
    assert report.urgent_tasks == 1
    assert len(january_tasks) == 1
    assert january_tasks[0].title == "Inspect dishwasher"


def test_delete_task_removes_row(session):
    svc = TaskService(session)
    task = svc.create_task(title="To remove", description="x")
    session.commit()

    svc.delete_task(task.id)
    session.commit()

    assert session.get(Task, task.id) is None
