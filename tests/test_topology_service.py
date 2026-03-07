import pytest
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from homepal.db import Base
from homepal.models import AssetRoomLink, LinkRole, TaskAssetLink, TaskRoomLink
from homepal.services.task_service import TaskService


def test_asset_primary_and_additional_room_links():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        svc = TaskService(session)
        kitchen = svc.create_room(name="Kitchen")
        bathroom = svc.create_room(name="Bathroom")

        asset = svc.create_asset(
            primary_room_id=kitchen.id,
            also_used_in_room_ids=[bathroom.id],
            name="Dehumidifier",
            category_code="ventilation_dehumidifier",
        )
        session.commit()

        links = session.query(AssetRoomLink).where(AssetRoomLink.asset_id == asset.id).all()
        assert len(links) == 2
        assert any(link.room_id == kitchen.id and link.is_primary for link in links)
        assert any(link.room_id == bathroom.id and not link.is_primary for link in links)


def test_task_room_and_asset_role_links():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        svc = TaskService(session)
        kitchen = svc.create_room(name="Kitchen")
        hall = svc.create_room(name="Hall")

        boiler = svc.create_asset(primary_room_id=kitchen.id, name="Boiler", category_code="heating_boiler")
        ladder = svc.create_asset(primary_room_id=hall.id, name="Ladder", category_code="tools_ladder")
        paint = svc.create_asset(primary_room_id=hall.id, name="Paint", category_code="materials_paint")

        task = svc.create_task(
            title="Fix ceiling",
            description="Repair kitchen plaster",
            room_ids=[kitchen.id, hall.id],
            about_asset_ids=[boiler.id],
            uses_asset_ids=[ladder.id],
            requires_assets=[(paint.id, Decimal("1.500"), "L")],
        )
        session.commit()

        room_links = session.query(TaskRoomLink).where(TaskRoomLink.task_id == task.id).all()
        assert {link.room_id for link in room_links} == {kitchen.id, hall.id}

        asset_links = session.query(TaskAssetLink).where(TaskAssetLink.task_id == task.id).all()
        roles = {(link.asset_id, link.role) for link in asset_links}
        assert (boiler.id, LinkRole.ABOUT) in roles
        assert (ladder.id, LinkRole.USES) in roles
        requires = next(link for link in asset_links if link.role == LinkRole.REQUIRES)
        assert requires.asset_id == paint.id
        assert requires.unit == "L"


def test_delete_asset_and_room_workflow():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        svc = TaskService(session)
        kitchen = svc.create_room(name="Kitchen")
        office = svc.create_room(name="Office")
        asset = svc.create_asset(primary_room_id=kitchen.id, also_used_in_room_ids=[office.id], name="Router", category_code="it_router")
        session.commit()

        with pytest.raises(ValueError):
            svc.delete_room(kitchen.id)

        svc.delete_asset(asset.id)
        session.commit()

        svc.delete_room(office.id)
        svc.delete_room(kitchen.id)
        session.commit()

        assert svc.list_rooms() == []
