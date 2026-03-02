# Alembic migrations

This folder contains Alembic migration scripts.

## Seed revisions

- `20260302_01_seed_asset_categories.py` seeds 70 baseline rows for the controlled `asset_categories` list.
- `20260302_02_seed_attribute_definitions.py` seeds global, category-scoped, and room-type-scoped rows for `attribute_definitions`.

These seeds use fixed UUIDs so upgrades are deterministic and downgrades can target known IDs.
