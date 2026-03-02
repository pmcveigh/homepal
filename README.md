# Homepal MVP Scaffold

Homepal is a native Linux desktop application for deterministic household operations management.
This repository contains an MVP-oriented scaffold aligned with the requested architecture:

- Python 3.12
- PySide6 (Qt Widgets)
- SQLite + SQLAlchemy ORM
- Alembic migration directory scaffold
- Service layer mediation between GUI and persistence

## Current Structure

```
homepal/
  models/
  services/
  views/
  widgets/
  migrations/
main.py
```

## Implemented MVP Foundations

- Domain models for Property, Room, Asset, Task, RecurringSchedule, Attachment, and TaskHistory.
- Priority enum and strict task workflow transition map.
- Transaction-safe recurring task cloning behavior in service logic.
- Backup service for 7-day prompt strategy and checksum-backed file copy.
- Main window with left navigation, stacked views, and status bar scaffold.
- Persistent local paths:
  - DB: `~/.local/share/homepal/homepal.db`
  - Config: `~/.config/homepal/config.toml`
  - Logs: `~/.local/share/homepal/logs/homepal.log`

## Running

```bash
python main.py
```

## Testing

```bash
pytest
```
