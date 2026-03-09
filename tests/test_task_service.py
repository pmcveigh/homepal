from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import (
    BudgetEntry,
    Priority,
    RecurrenceType,
    RecurringSchedule,
    ShoppingListItem,
    Task,
    TaskAssignment,
    TaskChecklistItem,
    TaskDependency,
    TaskProviderLink,
    TaskStatus,
)
from homepal.services.task_service import TaskEditorDTO, TaskService


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


def test_save_task_editor_with_required_asset_only(session):
    svc = TaskService(session)
    room = svc.create_room(name="Garage")
    asset = svc.create_asset(primary_room_id=room.id, name="Filter", category_code="hvac_filter")

    dto = TaskEditorDTO(
        title="Replace filter",
        description="",
        room_ids=[],
        requires_assets=[(asset.id, None, "seasonal replacement")],
    )
    created = svc.save_task_editor_dto(dto)
    session.commit()

    stored = session.get(Task, created.id)
    assert stored is not None
    assert stored.asset_id == asset.id


def test_create_task_supports_assignments_providers_materials_checklists_dependencies_and_budget(session):
    svc = TaskService(session)
    room = svc.create_room(name="Kitchen")
    member = svc.create_household_member(name="Alex")
    provider = svc.create_provider(name="Plumber Co", service_type="Plumbing")
    prerequisite = svc.create_task(title="Turn off water", description="", room_ids=[room.id])

    task = svc.create_task(
        title="Replace faucet",
        description="",
        room_ids=[room.id],
        assigned_member_ids=[member.id],
        provider_ids=[provider.id],
        required_materials=[("PTFE Tape", Decimal("1"), "roll")],
        checklist_items=["Shutoff verified", "Leak test"],
        dependency_task_ids=[prerequisite.id],
        estimated_cost=Decimal("45.50"),
    )
    session.commit()

    assert session.query(TaskAssignment).where(TaskAssignment.task_id == task.id).count() == 1
    assert session.query(TaskProviderLink).where(TaskProviderLink.task_id == task.id).count() == 1
    assert session.query(TaskChecklistItem).where(TaskChecklistItem.task_id == task.id).count() == 2
    assert session.query(TaskDependency).where(TaskDependency.task_id == task.id).count() == 1
    shopping = session.query(ShoppingListItem).where(ShoppingListItem.task_id == task.id).one()
    assert shopping.is_purchased is False
    budget = session.query(BudgetEntry).where(BudgetEntry.task_id == task.id).one()
    assert budget.amount == Decimal("45.50")


def test_dependency_blocks_task_start_until_complete(session):
    svc = TaskService(session)
    room = svc.create_room(name="Garage")
    task_a = svc.create_task(title="Prep", description="", room_ids=[room.id])
    task_b = svc.create_task(title="Do work", description="", room_ids=[room.id], dependency_task_ids=[task_a.id])

    with pytest.raises(ValueError, match="dependencies"):
        svc.transition_status(task_b, TaskStatus.IN_PROGRESS)

    svc.transition_status(task_a, TaskStatus.IN_PROGRESS)
    svc.transition_status(task_a, TaskStatus.COMPLETED)
    svc.transition_status(task_b, TaskStatus.IN_PROGRESS)
    session.commit()

    assert task_b.status == TaskStatus.IN_PROGRESS


def test_material_purchase_toggle_and_attachment(session):
    svc = TaskService(session)
    task = svc.create_task(title="Read manual", description="")
    material = svc.add_task_material(task_id=task.id, name="Manual sleeve", add_to_shopping=True)
    item = session.query(ShoppingListItem).where(ShoppingListItem.material_id == material.id).one()

    svc.set_material_purchased(item.id, True)
    attachment = svc.add_task_attachment(task.id, "docs/manual.pdf")
    session.commit()

    assert session.get(ShoppingListItem, item.id).is_purchased is True
    assert attachment.file_path == "docs/manual.pdf"


def test_new_recurrence_modes_compute_next_task(session):
    schedule = RecurringSchedule(recurrence_type=RecurrenceType.WEEKLY)
    task = Task(
        title="Water plants",
        description="",
        priority=Priority.P3,
        status=TaskStatus.IN_PROGRESS,
        room_id="room",
        recurring_schedule=schedule,
    )
    session.add_all([schedule, task])

    svc = TaskService(session)
    svc.transition_status(task, TaskStatus.COMPLETED)
    session.commit()

    created = session.query(Task).where(Task.parent_task_id == task.id).one()
    assert created.due_date == datetime.combine(date.today() + timedelta(days=7), time.min)
