from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import (
    AssetCategory,
    AssetRoomLink,
    AttributeDefinition,
    AttributeValue,
    LinkRole,
    Priority,
    Task,
    TaskAssetLink,
    TaskRoomLink,
    TaskStatus,
    ValueType,
)
from homepal.services.task_service import TaskEditorDTO, TaskListFilters, TaskService


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db


def test_create_room_trims_user_input_fields(session: Session):
    svc = TaskService(session)

    room = svc.create_room(name="  Living Room  ", description="  lounge  ", floor_level="  1  ")
    blank = svc.create_room(name=" Closet ", description="   ", floor_level="   ")
    session.commit()

    assert room.name == "Living Room"
    assert room.description == "lounge"
    assert room.floor_level == "1"
    assert blank.description is None
    assert blank.floor_level is None


def test_get_or_create_asset_category_normalizes_and_reuses_existing(session: Session):
    svc = TaskService(session)

    first = svc.get_or_create_asset_category("  HVAC_Filter  ")
    second = svc.get_or_create_asset_category("hvac_filter")
    session.commit()

    assert first.id == second.id
    assert first.code == "hvac_filter"
    assert first.display_name == "Hvac Filter"
    assert session.scalar(select(AssetCategory).where(AssetCategory.code == "hvac_filter")) is not None


def test_create_asset_deduplicates_primary_room_in_room_links(session: Session):
    svc = TaskService(session)
    kitchen = svc.create_room(name="Kitchen")
    garage = svc.create_room(name="Garage")

    asset = svc.create_asset(
        primary_room_id=kitchen.id,
        also_used_in_room_ids=[kitchen.id, garage.id, garage.id],
        name="Pressure Washer",
        category_code="cleaning_tools",
    )
    session.commit()

    links = session.query(AssetRoomLink).where(AssetRoomLink.asset_id == asset.id).all()
    assert len(links) == 2
    assert [link.room_id for link in links if link.is_primary] == [kitchen.id]


def test_set_asset_room_links_requires_primary_room_to_be_listed(session: Session):
    svc = TaskService(session)
    room_a = svc.create_room(name="A")
    room_b = svc.create_room(name="B")
    asset = svc.create_asset(primary_room_id=room_a.id, name="Router", category_code="network_router")

    with pytest.raises(ValueError, match="Primary room"):
        svc.set_asset_room_links(asset.id, primary_room_id=room_a.id, room_ids=[room_b.id])


def test_delete_room_rejects_when_tasks_still_linked(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Office")
    svc.create_task(title="Review bills", description="", room_ids=[room.id])
    session.commit()

    with pytest.raises(ValueError, match="linked tasks"):
        svc.delete_room(room.id)


def test_list_task_rows_filters_for_status_priority_room_asset_and_search(session: Session):
    svc = TaskService(session)
    kitchen = svc.create_room(name="Kitchen")
    garden = svc.create_room(name="Garden")
    boiler = svc.create_asset(primary_room_id=kitchen.id, name="Boiler", category_code="heating_boiler")
    mower = svc.create_asset(primary_room_id=garden.id, name="Mower", category_code="garden_mower")

    t1 = svc.create_task(
        title="Clean boiler filter",
        description="Monthly maintenance",
        priority=Priority.P1,
        room_ids=[kitchen.id],
        about_asset_ids=[boiler.id],
    )
    t2 = svc.create_task(
        title="Sharpen mower blade",
        description="Before spring",
        priority=Priority.P3,
        room_ids=[garden.id],
        about_asset_ids=[mower.id],
    )
    svc.transition_status(t1, TaskStatus.IN_PROGRESS)
    session.commit()

    rows = svc.list_task_rows(
        TaskListFilters(
            statuses=[TaskStatus.IN_PROGRESS],
            priorities=[Priority.P1],
            room_id=kitchen.id,
            asset_id=boiler.id,
            search="boiler",
        )
    )

    assert [row.id for row in rows] == [t1.id]
    assert rows[0].room_count == 1
    assert rows[0].asset_count == 1


def test_list_task_rows_due_ranges_cover_overdue_next7_and_next30(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Hall")
    today = date.today()

    overdue = svc.create_task(title="Overdue", description="", room_ids=[room.id], due_date=datetime.combine(today - timedelta(days=1), time.min))
    next_week = svc.create_task(title="Next Week", description="", room_ids=[room.id], due_date=datetime.combine(today + timedelta(days=3), time.min))
    next_month = svc.create_task(title="Next Month", description="", room_ids=[room.id], due_date=datetime.combine(today + timedelta(days=20), time.min))
    later = svc.create_task(title="Later", description="", room_ids=[room.id], due_date=datetime.combine(today + timedelta(days=40), time.min))
    session.commit()

    overdue_rows = svc.list_task_rows(TaskListFilters(due_range="overdue"))
    next7_rows = svc.list_task_rows(TaskListFilters(due_range="next7"))
    next30_rows = svc.list_task_rows(TaskListFilters(due_range="next30"))

    assert {row.id for row in overdue_rows} == {overdue.id}
    assert {row.id for row in next7_rows} == {next_week.id}
    assert {row.id for row in next30_rows} == {next_week.id, next_month.id}
    assert later.id not in {row.id for row in next30_rows}


def test_task_editor_round_trip_preserves_asset_roles_and_quantities(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Utility")
    about = svc.create_asset(primary_room_id=room.id, name="Water Heater", category_code="heater")
    used = svc.create_asset(primary_room_id=room.id, name="Wrench", category_code="tool")
    req = svc.create_asset(primary_room_id=room.id, name="Sealant", category_code="material")

    task = svc.create_task(
        title="Service heater",
        description="",
        room_ids=[room.id],
        about_asset_ids=[about.id],
        uses_asset_ids=[used.id],
        requires_assets=[(req.id, Decimal("0.250"), "kg")],
    )
    session.commit()

    dto = svc.get_task_editor_dto(task.id)

    assert dto.about_asset_ids == [about.id]
    assert dto.uses_asset_ids == [used.id]
    assert dto.requires_assets == [(req.id, Decimal("0.250"), "kg")]


def test_save_task_editor_updates_and_replaces_previous_links(session: Session):
    svc = TaskService(session)
    room_a = svc.create_room(name="A")
    room_b = svc.create_room(name="B")
    asset_a = svc.create_asset(primary_room_id=room_a.id, name="Asset A", category_code="a")
    asset_b = svc.create_asset(primary_room_id=room_b.id, name="Asset B", category_code="b")

    created = svc.save_task_editor_dto(
        TaskEditorDTO(
            title=" Initial Task ",
            description="  ",
            room_ids=[room_a.id],
            about_asset_ids=[asset_a.id],
        )
    )
    session.flush()

    updated = svc.save_task_editor_dto(
        TaskEditorDTO(
            id=created.id,
            title="Updated Task",
            description="changed",
            status=TaskStatus.BLOCKED,
            priority=Priority.P2,
            room_ids=[room_b.id],
            about_asset_ids=[asset_b.id],
            requires_assets=[],
        )
    )
    session.commit()

    room_links = session.query(TaskRoomLink).where(TaskRoomLink.task_id == updated.id).all()
    asset_links = session.query(TaskAssetLink).where(TaskAssetLink.task_id == updated.id).all()

    assert updated.description == "changed"
    assert updated.status == TaskStatus.BLOCKED
    assert {link.room_id for link in room_links} == {room_b.id}
    assert {(link.asset_id, link.role) for link in asset_links} == {(asset_b.id, LinkRole.ABOUT)}


def test_list_task_titles_for_room_separates_direct_and_asset_derived(session: Session):
    svc = TaskService(session)
    kitchen = svc.create_room(name="Kitchen")
    hall = svc.create_room(name="Hall")
    kettle = svc.create_asset(primary_room_id=kitchen.id, name="Kettle", category_code="appliance")

    direct_task = svc.create_task(title="Deep clean", description="", room_ids=[kitchen.id])
    derived_task = svc.create_task(title="Descale kettle", description="", room_ids=[hall.id], about_asset_ids=[kettle.id])
    uses_only_task = svc.create_task(title="Move kettle", description="", room_ids=[hall.id], uses_asset_ids=[kettle.id])
    session.commit()

    direct, derived = svc.list_task_titles_for_room(kitchen.id)

    assert {task.id for task in direct} == {direct_task.id}
    assert {task.id for task in derived} == {derived_task.id}
    assert uses_only_task.id not in {task.id for task in derived}


def test_suggest_primary_rooms_from_about_assets_returns_distinct_room_ids(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Kitchen")
    a1 = svc.create_asset(primary_room_id=room.id, name="Sink", category_code="plumbing")
    a2 = svc.create_asset(primary_room_id=room.id, name="Tap", category_code="plumbing")
    session.commit()

    suggested = svc.suggest_primary_rooms_from_about_assets([a1.id, a2.id])

    assert suggested == [room.id]


def test_list_assets_for_room_respects_portable_only_and_warranty_soon(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Garage")
    portable = svc.create_asset(primary_room_id=room.id, name="Drill", notes="portable", category_code="tools")
    fixed = svc.create_asset(primary_room_id=room.id, name="Heater", notes="wall mounted", category_code="heating")
    portable.warranty_expiry = date.today() + timedelta(days=10)
    fixed.warranty_expiry = date.today() + timedelta(days=120)
    session.commit()

    warranty_soon = svc.list_assets_for_room(room.id, warranty_soon=True)
    portable_only = svc.list_assets_for_room(room.id, portable_only=True)

    assert {item.id for item in warranty_soon} == {portable.id}
    assert {item.id for item in portable_only} == {portable.id}


def test_list_rooms_overview_search_type_and_counts(session: Session):
    svc = TaskService(session)
    kitchen = svc.create_room(name="Kitchen", description="kitchen")
    bedroom = svc.create_room(name="Bedroom", description="bedroom")
    svc.create_asset(primary_room_id=kitchen.id, name="Fridge", category_code="appliance")

    overdue = svc.create_task(
        title="Expired chore",
        description="",
        room_ids=[kitchen.id],
        due_date=datetime.combine(date.today() - timedelta(days=2), time.min),
    )
    open_task = svc.create_task(title="Fresh chore", description="", room_ids=[kitchen.id])
    svc.transition_status(open_task, TaskStatus.IN_PROGRESS)
    svc.transition_status(overdue, TaskStatus.BLOCKED)
    session.commit()

    kitchen_rows = svc.list_rooms_overview(search="Kit", room_type="kitchen")
    bedroom_rows = svc.list_rooms_overview(search="Bed", room_type="bedroom")

    assert len(kitchen_rows) == 1
    assert kitchen_rows[0].asset_count == 1
    assert kitchen_rows[0].open_tasks_count == 2
    assert kitchen_rows[0].overdue_tasks_count == 1
    assert len(bedroom_rows) == 1


def test_list_attribute_definitions_prioritizes_most_specific_scope(session: Session):
    svc = TaskService(session)
    specific_cat = svc.get_or_create_asset_category("heating")

    generic_asset = AttributeDefinition(
        applies_to="asset",
        category_id=None,
        key="condition",
        display_name="Condition",
        value_type=ValueType.TEXT,
    )
    specific_asset = AttributeDefinition(
        applies_to="asset",
        category_id=specific_cat.id,
        key="burner_type",
        display_name="Burner Type",
        value_type=ValueType.TEXT,
    )
    any_room = AttributeDefinition(
        applies_to="room",
        room_type="any",
        key="paint",
        display_name="Paint",
        value_type=ValueType.TEXT,
    )
    kitchen_room = AttributeDefinition(
        applies_to="room",
        room_type="kitchen",
        key="worktop",
        display_name="Worktop",
        value_type=ValueType.TEXT,
    )
    session.add_all([generic_asset, specific_asset, any_room, kitchen_room])
    session.commit()

    asset_defs = svc.list_attribute_definitions(applies_to="asset", category_id=specific_cat.id)
    room_defs = svc.list_attribute_definitions(applies_to="room", room_type="kitchen")

    assert [item.id for item in asset_defs] == [specific_asset.id, generic_asset.id]
    assert [item.id for item in room_defs] == [kitchen_room.id, any_room.id]


def test_upsert_and_get_attribute_values_handle_types_and_stale_rows(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Utility")

    text_def = AttributeDefinition(applies_to="room", room_type="any", key="finish", display_name="Finish", value_type=ValueType.TEXT)
    int_def = AttributeDefinition(applies_to="room", room_type="any", key="windows", display_name="Windows", value_type=ValueType.INT)
    dec_def = AttributeDefinition(applies_to="room", room_type="any", key="area", display_name="Area", value_type=ValueType.DECIMAL)
    bool_def = AttributeDefinition(applies_to="room", room_type="any", key="heated", display_name="Heated", value_type=ValueType.BOOL)
    date_def = AttributeDefinition(applies_to="room", room_type="any", key="inspected", display_name="Inspected", value_type=ValueType.DATE)
    session.add_all([text_def, int_def, dec_def, bool_def, date_def])
    session.flush()

    svc.upsert_attribute_values(
        owner_type="room",
        owner_id=room.id,
        values={
            text_def.id: "matte",
            int_def.id: 2,
            dec_def.id: Decimal("12.75"),
            bool_def.id: True,
            date_def.id: date(2026, 1, 7),
        },
        active_definition_ids=[text_def.id, int_def.id, dec_def.id, bool_def.id, date_def.id],
        definitions=[text_def, int_def, dec_def, bool_def, date_def],
    )
    session.flush()

    values = svc.get_attribute_values(owner_type="room", owner_id=room.id)
    assert values[text_def.id] == "matte"
    assert values[int_def.id] == 2
    assert values[dec_def.id] == 12.75
    assert values[bool_def.id] is True
    assert values[date_def.id] == date(2026, 1, 7)

    svc.upsert_attribute_values(
        owner_type="room",
        owner_id=room.id,
        values={text_def.id: "gloss"},
        active_definition_ids=[text_def.id],
        definitions=[text_def],
    )
    session.commit()

    persisted = session.query(AttributeValue).where(AttributeValue.room_id == room.id).all()
    assert len(persisted) == 1
    assert persisted[0].definition_id == text_def.id


def test_list_task_links_for_asset_groups_by_each_link_role(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Study")
    asset = svc.create_asset(primary_room_id=room.id, name="Desk", category_code="furniture")

    about = svc.create_task(title="Inspect desk", description="", room_ids=[room.id], about_asset_ids=[asset.id])
    uses = svc.create_task(title="Use desk", description="", room_ids=[room.id], uses_asset_ids=[asset.id])
    requires = svc.create_task(title="Repair desk", description="", room_ids=[room.id], requires_assets=[(asset.id, Decimal("1.0"), "pc")])
    session.commit()

    grouped = svc.list_task_links_for_asset(asset.id)

    assert {task.id for task in grouped[LinkRole.ABOUT]} == {about.id}
    assert {task.id for task in grouped[LinkRole.USES]} == {uses.id}
    assert {task.id for task in grouped[LinkRole.REQUIRES]} == {requires.id}


def test_delete_asset_cleans_related_links_and_task_pointer(session: Session):
    svc = TaskService(session)
    room = svc.create_room(name="Laundry")
    asset = svc.create_asset(primary_room_id=room.id, name="Washer", category_code="appliance")
    task = svc.create_task(title="Check washer", description="", room_ids=[room.id], about_asset_ids=[asset.id])
    session.commit()

    svc.delete_asset(asset.id)
    session.commit()

    refreshed = session.get(Task, task.id)
    remaining_links = session.query(TaskAssetLink).where(TaskAssetLink.task_id == task.id).all()

    assert refreshed is not None
    assert refreshed.asset_id is None
    assert remaining_links == []
