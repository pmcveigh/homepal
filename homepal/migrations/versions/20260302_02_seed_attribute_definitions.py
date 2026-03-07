"""seed attribute definitions

Revision ID: 20260302_02
Revises: 20260302_01
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_02"
down_revision = "20260302_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
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

    cat = {
        "heating_boiler": "00000000-0000-0000-0000-000000000023",
        "it_router": "00000000-0000-0000-0000-000000000046",
        "it_wifi_extender": "00000000-0000-0000-0000-000000000047",
        "ventilation_dehumidifier": "00000000-0000-0000-0000-000000000035",
        "ventilation_extractor_fan": "00000000-0000-0000-0000-000000000034",
        "safety_smoke_alarm": "00000000-0000-0000-0000-000000000031",
        "safety_co_alarm": "00000000-0000-0000-0000-000000000033",
        "materials_paint": "00000000-0000-0000-0000-000000000059",
        "building_flooring": "00000000-0000-0000-0000-000000000007",
    }

    rows = []

    def add_asset_global(
        i: int,
        key: str,
        display: str,
        vtype: str,
        unit: str | None = None,
        choices: str | None = None,
        required: bool = False,
        searchable: bool = True,
        filterable: bool = True,
    ) -> None:
        rows.append(
            {
                "id": f"10000000-0000-0000-0000-000000000{str(i).zfill(3)}",
                "applies_to": "asset",
                "category_id": None,
                "room_type": None,
                "key": key,
                "display_name": display,
                "value_type": vtype,
                "unit": unit,
                "choices_csv": choices,
                "required": required,
                "searchable": searchable,
                "filterable": filterable,
            }
        )

    def add_asset_cat(
        i: int,
        category_code: str,
        key: str,
        display: str,
        vtype: str,
        unit: str | None = None,
        choices: str | None = None,
        required: bool = False,
        searchable: bool = False,
        filterable: bool = True,
    ) -> None:
        rows.append(
            {
                "id": f"20000000-0000-0000-0000-000000000{str(i).zfill(3)}",
                "applies_to": "asset",
                "category_id": cat[category_code],
                "room_type": None,
                "key": key,
                "display_name": display,
                "value_type": vtype,
                "unit": unit,
                "choices_csv": choices,
                "required": required,
                "searchable": searchable,
                "filterable": filterable,
            }
        )

    def add_room_type(
        i: int,
        room_type: str,
        key: str,
        display: str,
        vtype: str,
        unit: str | None = None,
        choices: str | None = None,
        required: bool = False,
        searchable: bool = False,
        filterable: bool = True,
    ) -> None:
        rows.append(
            {
                "id": f"30000000-0000-0000-0000-000000000{str(i).zfill(3)}",
                "applies_to": "room",
                "category_id": None,
                "room_type": room_type,
                "key": key,
                "display_name": display,
                "value_type": vtype,
                "unit": unit,
                "choices_csv": choices,
                "required": required,
                "searchable": searchable,
                "filterable": filterable,
            }
        )

    add_asset_global(1, "manufacturer", "Manufacturer", "text")
    add_asset_global(2, "model", "Model", "text")
    add_asset_global(3, "serial_number", "Serial number", "text")
    add_asset_global(
        4,
        "condition",
        "Condition",
        "choice",
        choices="new,opened,used,heavily_used,spares_only",
        required=True,
        searchable=False,
        filterable=True,
    )
    add_asset_global(5, "is_portable", "Portable", "bool", searchable=False)
    add_asset_global(6, "storage_location", "Storage location", "text")
    add_asset_global(7, "last_service_date", "Last service date", "date", searchable=False)
    add_asset_global(
        8,
        "service_interval_months",
        "Service interval",
        "int",
        unit="months",
        searchable=False,
    )
    add_asset_global(9, "manual_url", "Manual URL", "text", searchable=False, filterable=False)
    add_asset_global(10, "energy_rating", "Energy rating", "choice", choices="A,B,C,D,E,F", searchable=False)

    add_asset_cat(1, "heating_boiler", "fuel_type", "Fuel type", "choice", choices="gas,oil,electric,other", required=True)
    add_asset_cat(2, "heating_boiler", "boiler_type", "Boiler type", "choice", choices="combi,system,regular,other", required=True)
    add_asset_cat(3, "heating_boiler", "output_kw", "Output", "decimal", unit="kW")
    add_asset_cat(4, "heating_boiler", "installer", "Installer", "text")
    add_asset_cat(5, "heating_boiler", "service_company", "Service company", "text")
    add_asset_cat(6, "heating_boiler", "next_service_due", "Next service due", "date")

    add_asset_cat(20, "ventilation_dehumidifier", "capacity_l_per_day", "Capacity", "decimal", unit="L/day")
    add_asset_cat(21, "ventilation_dehumidifier", "tank_size_l", "Tank size", "decimal", unit="L")
    add_asset_cat(22, "ventilation_dehumidifier", "has_humidistat", "Humidistat", "bool")
    add_asset_cat(23, "ventilation_dehumidifier", "filter_type", "Filter type", "text")

    add_asset_cat(40, "ventilation_extractor_fan", "fan_type", "Fan type", "choice", choices="axial,centrifugal,inline,other")
    add_asset_cat(41, "ventilation_extractor_fan", "timer_overrun", "Timer overrun", "bool")
    add_asset_cat(42, "ventilation_extractor_fan", "rate_m3_h", "Extraction rate", "decimal", unit="m3/h")
    add_asset_cat(43, "ventilation_extractor_fan", "noise_db", "Noise level", "decimal", unit="dB")

    add_asset_cat(60, "it_router", "wan_type", "WAN type", "choice", choices="dsl,fttp,ethernet,other")
    add_asset_cat(61, "it_router", "wifi_standard", "Wi-Fi standard", "choice", choices="wifi4,wifi5,wifi6,wifi6e,wifi7")
    add_asset_cat(62, "it_router", "supports_mesh", "Mesh support", "bool")
    add_asset_cat(63, "it_router", "supports_wpa3", "WPA3", "bool")
    add_asset_cat(64, "it_router", "lan_ports", "LAN ports", "int")

    add_asset_cat(80, "it_wifi_extender", "backhaul_type", "Backhaul type", "choice", choices="wireless,ethernet,mocha,other")
    add_asset_cat(81, "it_wifi_extender", "supports_mlo", "MLO support", "bool")
    add_asset_cat(82, "it_wifi_extender", "wifi_standard", "Wi-Fi standard", "choice", choices="wifi4,wifi5,wifi6,wifi6e,wifi7")
    add_asset_cat(83, "it_wifi_extender", "placement_height", "Placement height", "decimal", unit="m")

    add_asset_cat(100, "safety_smoke_alarm", "power_source", "Power source", "choice", choices="battery,mains,hybrid")
    add_asset_cat(101, "safety_smoke_alarm", "interlinked", "Interlinked", "bool")
    add_asset_cat(102, "safety_smoke_alarm", "last_test_date", "Last test date", "date")
    add_asset_cat(103, "safety_smoke_alarm", "replace_by_date", "Replace by date", "date")

    add_asset_cat(120, "safety_co_alarm", "power_source", "Power source", "choice", choices="battery,mains,hybrid")
    add_asset_cat(121, "safety_co_alarm", "last_test_date", "Last test date", "date")
    add_asset_cat(122, "safety_co_alarm", "replace_by_date", "Replace by date", "date")

    add_asset_cat(140, "materials_paint", "paint_type", "Paint type", "choice", choices="emulsion,eggshell,satin,gloss,primer,undercoat,other")
    add_asset_cat(141, "materials_paint", "finish", "Finish", "choice", choices="matt,silk,satin,gloss")
    add_asset_cat(142, "materials_paint", "colour_name", "Colour name", "text")
    add_asset_cat(143, "materials_paint", "volume_l", "Volume", "decimal", unit="L")
    add_asset_cat(144, "materials_paint", "coverage_m2_per_l", "Coverage", "decimal", unit="m2/L")

    add_asset_cat(160, "building_flooring", "flooring_type", "Flooring type", "choice", choices="carpet,laminate,vinyl,wood,tile,other")
    add_asset_cat(161, "building_flooring", "underlay_type", "Underlay type", "text")
    add_asset_cat(162, "building_flooring", "installed_date", "Installed date", "date")
    add_asset_cat(163, "building_flooring", "area_m2", "Area", "decimal", unit="m2")

    add_room_type(1, "any", "dimensions_m2", "Floor area", "decimal", unit="m2")
    add_room_type(2, "any", "ceiling_height_m", "Ceiling height", "decimal", unit="m")
    add_room_type(3, "any", "flooring_type", "Flooring type", "choice", choices="carpet,laminate,vinyl,wood,tile,other")
    add_room_type(4, "any", "last_decorated", "Last decorated", "date")

    add_room_type(20, "bathroom", "has_extractor", "Extractor present", "bool")
    add_room_type(21, "bathroom", "extractor_type", "Extractor type", "choice", choices="axial,centrifugal,inline,other")
    add_room_type(22, "bathroom", "mould_risk", "Mould risk", "choice", choices="low,medium,high")
    add_room_type(23, "bathroom", "last_mould_treatment", "Last mould treatment", "date")
    add_room_type(24, "bathroom", "has_window", "Window present", "bool")

    add_room_type(40, "kitchen", "cooker_type", "Cooker type", "choice", choices="gas,electric,induction,other")
    add_room_type(41, "kitchen", "has_hood", "Extractor hood present", "bool")
    add_room_type(
        42,
        "kitchen",
        "worktop_material",
        "Worktop material",
        "choice",
        choices="laminate,wood,stone,composite,stainless_steel,other",
    )

    add_room_type(60, "bedroom", "has_blackout_blinds", "Blackout blinds", "bool")
    add_room_type(61, "bedroom", "damp_risk", "Damp risk", "choice", choices="low,medium,high")

    op.bulk_insert(attribute_definitions, rows)


def downgrade() -> None:
    op.execute("DELETE FROM attribute_definitions WHERE id LIKE '10000000-0000-0000-0000-000000000%'")
    op.execute("DELETE FROM attribute_definitions WHERE id LIKE '20000000-0000-0000-0000-000000000%'")
    op.execute("DELETE FROM attribute_definitions WHERE id LIKE '30000000-0000-0000-0000-000000000%'")
