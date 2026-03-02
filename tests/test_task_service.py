from datetime import date, timedelta

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
    assert new_task.due_date == date.today() + timedelta(days=30)


def test_dashboard_stats_counts(session):
    today = date(2026, 1, 10)
    session.add_all(
        [
            Task(title="Open overdue", description="d", priority=Priority.P1, status=TaskStatus.OPEN, room_id="r", due_date=today - timedelta(days=1)),
            Task(title="In progress", description="d", priority=Priority.P2, status=TaskStatus.IN_PROGRESS, room_id="r", due_date=today + timedelta(days=2)),
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
    created = svc.create_task(title="Replace bulbs", description="Hallway lights")
    session.commit()

    stored = session.get(Task, created.id)
    assert stored is not None
    assert stored.room_id is not None
    assert stored.status == TaskStatus.OPEN
