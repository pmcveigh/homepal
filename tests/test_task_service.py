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
    schedule = RecurringSchedule(recurrence_type=RecurrenceType.EVERY_N_DAYS, interval_value=30)
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
    assert new_task.due_date == date.today() + timedelta(days=30)
