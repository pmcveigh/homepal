from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import Priority, RecurrenceType, TaskStatus
from homepal.services.task_service import TaskListFilters, TaskService


def setup_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_filters_and_sorting_by_room_member_provider_status_due():
    with setup_session() as session:
        svc = TaskService(session)
        room1 = svc.create_room(name="Kitchen")
        room2 = svc.create_room(name="Garage")
        member = svc.create_household_member(name="Alex")
        provider = svc.create_provider(name="Spark Co", service_type="Electrical")
        asset = svc.create_asset(primary_room_id=room1.id, name="Dishwasher", category_code="appliance")

        svc.create_task(title="Overdue", description="", room_ids=[room1.id], assigned_member_ids=[member.id], provider_ids=[provider.id], due_date=datetime(2026, 1, 1), priority=Priority.P1)
        svc.create_task(title="Future", description="", room_ids=[room2.id], about_asset_ids=[asset.id], due_date=datetime(2099, 1, 1), priority=Priority.P4)
        session.commit()

        rows = svc.list_task_rows(TaskListFilters(room_id=room1.id, member_id=member.id, provider_id=provider.id, statuses=[TaskStatus.OPEN]))
        assert len(rows) == 1
        assert rows[0].title == "Overdue"


def test_duplicate_template_and_recurring_generation():
    with setup_session() as session:
        svc = TaskService(session)
        room = svc.create_room(name="Hall")
        template = svc.create_task(
            title="Change filter",
            description="",
            room_ids=[room.id],
            recurrence_type=RecurrenceType.WEEKLY,
            is_template=True,
        )
        session.commit()

        copied = svc.duplicate_task(template.id, as_template=False)
        assert copied.id != template.id
        assert copied.is_template is False

        created = svc.generate_recurring_tasks(as_of=date(2026, 1, 10))
        assert created == 1
        generated = svc.list_task_rows(TaskListFilters(search="Change filter", include_templates=False))
        assert any(r.title.startswith("Change filter") for r in generated)


def test_grouping_and_due_highlights():
    with setup_session() as session:
        svc = TaskService(session)
        room = svc.create_room(name="Office")
        member = svc.create_household_member(name="Jamie")
        svc.create_task(title="Today", description="", room_ids=[room.id], assigned_member_ids=[member.id], due_date=datetime.now())
        session.commit()

        by_room = svc.list_tasks_grouped_by_room()
        by_member = svc.list_tasks_grouped_by_member()
        overdue, today, week = svc.get_due_highlights()

        assert "Office" in by_room
        assert "Jamie" in by_member
        assert len(today) >= 1
        assert len(week) >= 1
        assert isinstance(overdue, list)
