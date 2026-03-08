"""expand asset and room classifications

Revision ID: 20260307_03
Revises: 20260302_02
Create Date: 2026-03-07
"""

from alembic import op
import sqlalchemy as sa


revision = "20260307_03"
down_revision = "20260302_02"
branch_labels = None
depends_on = None


ASSET_CATEGORY_ROWS = [
    {"id": "00000000-0000-0000-0000-000000000101", "code": "security_cctv_nvr", "display_name": "CCTV NVR", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000102", "code": "security_motion_sensor", "display_name": "Motion sensor", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000103", "code": "security_window_sensor", "display_name": "Window sensor", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000104", "code": "water_leak_detector", "display_name": "Leak detector", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000105", "code": "water_shutoff_valve", "display_name": "Smart shutoff valve", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000106", "code": "garden_rainwater_harvester", "display_name": "Rainwater harvester", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000107", "code": "outdoor_pergola", "display_name": "Pergola", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000108", "code": "appliance_tumble_dryer", "display_name": "Tumble dryer", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000109", "code": "appliance_wine_cooler", "display_name": "Wine cooler", "is_active": True},
    {"id": "00000000-0000-0000-0000-000000000110", "code": "storage_bike_rack", "display_name": "Bike rack", "is_active": True},
]

ATTRIBUTE_DEFINITION_ROWS = [
    {
        "id": "31000000-0000-0000-0000-000000000001",
        "applies_to": "room",
        "category_id": None,
        "room_type": "living_room",
        "key": "has_fireplace",
        "display_name": "Fireplace present",
        "value_type": "bool",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000002",
        "applies_to": "room",
        "category_id": None,
        "room_type": "living_room",
        "key": "seating_capacity",
        "display_name": "Seating capacity",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000003",
        "applies_to": "room",
        "category_id": None,
        "room_type": "dining_room",
        "key": "table_capacity",
        "display_name": "Dining table capacity",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000004",
        "applies_to": "room",
        "category_id": None,
        "room_type": "dining_room",
        "key": "has_sideboard",
        "display_name": "Sideboard present",
        "value_type": "bool",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000005",
        "applies_to": "room",
        "category_id": None,
        "room_type": "office",
        "key": "desk_count",
        "display_name": "Desk count",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000006",
        "applies_to": "room",
        "category_id": None,
        "room_type": "office",
        "key": "network_ports",
        "display_name": "Network ports",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000007",
        "applies_to": "room",
        "category_id": None,
        "room_type": "garage",
        "key": "vehicle_capacity",
        "display_name": "Vehicle capacity",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000008",
        "applies_to": "room",
        "category_id": None,
        "room_type": "garage",
        "key": "door_type",
        "display_name": "Garage door type",
        "value_type": "choice",
        "unit": None,
        "choices_csv": "up_and_over,roller,sectional,side_hinged,other",
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000009",
        "applies_to": "room",
        "category_id": None,
        "room_type": "utility",
        "key": "has_drain",
        "display_name": "Floor drain present",
        "value_type": "bool",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000010",
        "applies_to": "room",
        "category_id": None,
        "room_type": "utility",
        "key": "storage_shelves",
        "display_name": "Storage shelves",
        "value_type": "int",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000011",
        "applies_to": "room",
        "category_id": None,
        "room_type": "laundry",
        "key": "has_vented_dryer",
        "display_name": "Vented dryer",
        "value_type": "bool",
        "unit": None,
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
    {
        "id": "31000000-0000-0000-0000-000000000012",
        "applies_to": "room",
        "category_id": None,
        "room_type": "laundry",
        "key": "counter_space_m",
        "display_name": "Counter space",
        "value_type": "decimal",
        "unit": "m",
        "choices_csv": None,
        "required": False,
        "searchable": False,
        "filterable": True,
    },
]


def upgrade() -> None:
    asset_categories = sa.table(
        "asset_categories",
        sa.column("id", sa.String(36)),
        sa.column("code", sa.String(60)),
        sa.column("display_name", sa.String(120)),
        sa.column("is_active", sa.Boolean),
    )
    attribute_definitions = sa.table(
        "attribute_definitions",
        sa.column("id", sa.String(36)),
        sa.column("applies_to", sa.String(10)),
        sa.column("category_id", sa.String(36)),
        sa.column("room_type", sa.String(40)),
        sa.column("key", sa.String(80)),
        sa.column("display_name", sa.String(120)),
        sa.column("value_type", sa.String(20)),
        sa.column("unit", sa.String(20)),
        sa.column("choices_csv", sa.Text),
        sa.column("required", sa.Boolean),
        sa.column("searchable", sa.Boolean),
        sa.column("filterable", sa.Boolean),
    )

    op.bulk_insert(asset_categories, ASSET_CATEGORY_ROWS)
    op.bulk_insert(attribute_definitions, ATTRIBUTE_DEFINITION_ROWS)


def downgrade() -> None:
    op.execute(
        "DELETE FROM attribute_definitions WHERE id BETWEEN '31000000-0000-0000-0000-000000000001' AND '31000000-0000-0000-0000-000000000999'"
    )
    op.execute(
        "DELETE FROM asset_categories WHERE id BETWEEN '00000000-0000-0000-0000-000000000101' AND '00000000-0000-0000-0000-000000000110'"
    )
