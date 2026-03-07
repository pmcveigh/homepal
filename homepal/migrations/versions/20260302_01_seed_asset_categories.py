"""seed asset categories

Revision ID: 20260302_01
Revises: 
Create Date: 2026-03-02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260302_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    asset_categories = sa.table(
        "asset_categories",
        sa.column("id", sa.String(36)),
        sa.column("code", sa.String(60)),
        sa.column("display_name", sa.String(120)),
        sa.column("is_active", sa.Boolean),
    )

    op.bulk_insert(
        asset_categories,
        [
            {"id": "00000000-0000-0000-0000-000000000001", "code": "building_roof", "display_name": "Roof", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000002", "code": "building_guttering", "display_name": "Guttering", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000003", "code": "building_downpipes", "display_name": "Downpipes", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000004", "code": "building_external_walls", "display_name": "External walls", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000005", "code": "building_internal_walls", "display_name": "Internal walls", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000006", "code": "building_ceiling", "display_name": "Ceiling", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000007", "code": "building_flooring", "display_name": "Flooring", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000008", "code": "building_insulation", "display_name": "Insulation", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000009", "code": "building_windows", "display_name": "Windows", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000010", "code": "building_doors", "display_name": "Doors", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000011", "code": "building_stairs", "display_name": "Stairs", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000012", "code": "building_fireplace", "display_name": "Fireplace / hearth", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000013", "code": "building_tiles_grout", "display_name": "Tiles and grout", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000014", "code": "building_sealants", "display_name": "Sealants", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000015", "code": "plumbing_taps", "display_name": "Taps", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000016", "code": "plumbing_sink_basin", "display_name": "Sink / basin", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000017", "code": "plumbing_toilet", "display_name": "Toilet / cistern", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000018", "code": "plumbing_bath", "display_name": "Bath", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000019", "code": "plumbing_shower_unit", "display_name": "Shower unit", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000020", "code": "plumbing_shower_head", "display_name": "Shower head", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000021", "code": "plumbing_radiator", "display_name": "Radiator", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000022", "code": "plumbing_pipework", "display_name": "Pipework", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000023", "code": "heating_boiler", "display_name": "Boiler", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000024", "code": "heating_thermostat", "display_name": "Thermostat / controller", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000025", "code": "heating_hot_water_cylinder", "display_name": "Hot water cylinder", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000026", "code": "electrical_consumer_unit", "display_name": "Consumer unit", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000027", "code": "electrical_sockets", "display_name": "Sockets", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000028", "code": "electrical_switches", "display_name": "Switches", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000029", "code": "electrical_lighting_fittings", "display_name": "Lighting fittings", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000030", "code": "electrical_spotlights", "display_name": "Spotlights", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000031", "code": "safety_smoke_alarm", "display_name": "Smoke alarm", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000032", "code": "safety_heat_alarm", "display_name": "Heat alarm", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000033", "code": "safety_co_alarm", "display_name": "Carbon monoxide alarm", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000034", "code": "ventilation_extractor_fan", "display_name": "Extractor fan", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000035", "code": "ventilation_dehumidifier", "display_name": "Dehumidifier", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000036", "code": "ventilation_air_purifier", "display_name": "Air purifier", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000037", "code": "kitchen_fridge_freezer", "display_name": "Fridge / freezer", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000038", "code": "kitchen_dishwasher", "display_name": "Dishwasher", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000039", "code": "kitchen_oven", "display_name": "Oven", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000040", "code": "kitchen_hob", "display_name": "Hob", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000041", "code": "kitchen_microwave", "display_name": "Microwave", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000042", "code": "kitchen_kettle", "display_name": "Kettle", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000043", "code": "kitchen_coffee_machine", "display_name": "Coffee machine", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000044", "code": "laundry_washing_machine", "display_name": "Washing machine", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000045", "code": "laundry_tumble_dryer", "display_name": "Tumble dryer", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000046", "code": "it_router", "display_name": "Router", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000047", "code": "it_wifi_extender", "display_name": "Wi-Fi extender / mesh node", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000048", "code": "it_switch", "display_name": "Network switch", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000049", "code": "it_nas", "display_name": "NAS / storage", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000050", "code": "security_camera", "display_name": "Security camera", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000051", "code": "security_alarm", "display_name": "Alarm system", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000052", "code": "garden_shed", "display_name": "Shed", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000053", "code": "garden_lawnmower", "display_name": "Lawnmower", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000054", "code": "garden_pressure_washer", "display_name": "Pressure washer", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000055", "code": "tools_ladder", "display_name": "Ladder", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000056", "code": "tools_drill", "display_name": "Drill", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000057", "code": "tools_sander", "display_name": "Sander", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000058", "code": "tools_scraper", "display_name": "Scraper", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000059", "code": "materials_paint", "display_name": "Paint", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000060", "code": "materials_filler", "display_name": "Filler", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000061", "code": "materials_silicone_sealant", "display_name": "Silicone sealant", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000062", "code": "materials_grout", "display_name": "Grout", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000063", "code": "materials_sandpaper", "display_name": "Sandpaper", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000064", "code": "materials_screws_fixings", "display_name": "Screws and fixings", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000065", "code": "cleaning_mould_remover", "display_name": "Mould remover", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000066", "code": "cleaning_bleach", "display_name": "Bleach", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000067", "code": "cleaning_descaler", "display_name": "Descaler", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000068", "code": "furniture_sofa", "display_name": "Sofa", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000069", "code": "furniture_bed", "display_name": "Bed", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000070", "code": "furniture_wardrobe", "display_name": "Wardrobe", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000071", "code": "furniture_dining_table", "display_name": "Dining table", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000072", "code": "furniture_office_chair", "display_name": "Office chair", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000073", "code": "furniture_bookshelf", "display_name": "Bookshelf", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000074", "code": "electrical_ev_charger", "display_name": "EV charger", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000075", "code": "electrical_solar_inverter", "display_name": "Solar inverter", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000076", "code": "electrical_battery_storage", "display_name": "Battery storage", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000077", "code": "heating_heat_pump", "display_name": "Heat pump", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000078", "code": "heating_underfloor_heating", "display_name": "Underfloor heating", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000079", "code": "ventilation_mvhr", "display_name": "MVHR unit", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000080", "code": "water_softener", "display_name": "Water softener", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000081", "code": "plumbing_sump_pump", "display_name": "Sump pump", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000082", "code": "security_smart_lock", "display_name": "Smart lock", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000083", "code": "security_video_doorbell", "display_name": "Video doorbell", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000084", "code": "garden_irrigation_system", "display_name": "Irrigation system", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000085", "code": "garden_greenhouse", "display_name": "Greenhouse", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000086", "code": "garden_compost_bin", "display_name": "Compost bin", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000087", "code": "outdoor_fence", "display_name": "Fence", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000088", "code": "outdoor_gate", "display_name": "Gate", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000089", "code": "outdoor_decking", "display_name": "Decking", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000090", "code": "outdoor_patio", "display_name": "Patio", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000091", "code": "pool_pump", "display_name": "Pool pump", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000092", "code": "pool_filter", "display_name": "Pool filter", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000093", "code": "appliance_air_conditioner", "display_name": "Air conditioner", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000094", "code": "appliance_vacuum_cleaner", "display_name": "Vacuum cleaner", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000095", "code": "appliance_robot_vacuum", "display_name": "Robot vacuum", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000096", "code": "appliance_iron", "display_name": "Iron", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000097", "code": "it_printer", "display_name": "Printer", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000098", "code": "it_ups", "display_name": "UPS", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000099", "code": "fire_sprinkler_system", "display_name": "Sprinkler system", "is_active": True},
            {"id": "00000000-0000-0000-0000-000000000100", "code": "storage_safe", "display_name": "Safe", "is_active": True},
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM asset_categories WHERE id BETWEEN '00000000-0000-0000-0000-000000000001' AND '00000000-0000-0000-0000-000000000100'"
    )
