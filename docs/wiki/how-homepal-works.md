# Homepal Architecture & Python Project Setup

This page explains how the current Homepal codebase is wired end-to-end, what Python libraries are used, how the project is set up, and why the implementation chose these paths over alternatives.

## 1) High-level runtime flow (from app launch to UI actions)

1. `main.py` bootstraps filesystem paths (`~/.local/share/homepal`, `~/.config/homepal`) and log directories before anything else.
2. Logging is configured with a rotating file handler (`homepal.log`).
3. The SQLite engine is created with SQLite pragmas (`WAL`, `foreign_keys=ON`) and an integrity check is run.
4. SQLAlchemy metadata tables are created (for scaffold/dev safety).
5. A Qt `QApplication` is launched and one SQLAlchemy session is created.
6. Seeded reference data (`asset_categories`, `attribute_definitions`) is verified before opening the UI.
7. `MainWindow` is created with one shared `TaskService` and all panels read/write through that service.

This creates a deterministic startup sequence where storage and seed guarantees exist before interactive usage begins, reducing runtime surprises and UI-level failure handling complexity.

## 2) Architectural layers and how they fit together

### 2.1 Entry point and composition root

- `main.py` is effectively the composition root: it instantiates infra (`engine`, session), service (`TaskService`), and view (`MainWindow`).
- This keeps dependency wiring centralized instead of being spread across widgets.

**Why this path?**
- For a desktop MVP, a single composition root is simpler to reason about than introducing a full dependency injection container.
- Alternative: a DI framework or custom service locator. We avoided this because the object graph is small and explicit constructors are clearer.

### 2.2 Persistence + domain model

- `homepal/db.py` defines SQLAlchemy `Base`, engine creation, session factory, and DB health check.
- `homepal/models/core.py` defines all domain entities and enums (tasks, rooms, assets, recurrence, links, metadata, history).
- Many-to-many relationships are represented using explicit link tables (`TaskRoomLink`, `TaskAssetLink`, `AssetRoomLink`) to preserve semantics and metadata (e.g., asset link role and quantity).

**Why this path?**
- Explicit link tables are more verbose than implicit many-to-many helpers, but they support richer semantics (`ABOUT` vs `USES` vs `REQUIRES`, plus units/quantities) and future extensibility.
- SQLAlchemy ORM gives strong schema expressiveness with Python typing; compared to raw SQL it improves maintainability and business-rule centralization.

### 2.3 Service layer

- `TaskService` is the central application service containing domain workflows (status transitions, recurring task cloning, reports, room/asset/task CRUD, link synchronization, history writes).
- `RoomService` and `AssetService` are thin adapters around `TaskService`, mainly shaping DTOs for UI usage.

**Why this path?**
- We intentionally keep business logic out of Qt widgets so UI components remain presentation-focused.
- Alternative: each widget directly manipulating ORM entities. We avoided that because it duplicates rules and makes testing harder.
- Slightly uncommon choice: one broad service (`TaskService`) owning many operations rather than many micro-services. For the current MVP scope this reduces coordination overhead and keeps cross-entity workflows (task-room-asset links) consistent in one place.

### 2.4 Presentation layer (Qt Widgets)

- `MainWindow` owns navigation and a stacked panel layout (Dashboard, Tasks, Rooms & Assets, Reports, Calendar, Settings placeholder).
- Panels invoke service methods and refresh via explicit signals (`data_changed`) and `refresh_views()`.

**Why this path?**
- Qt Widgets was chosen over web/Electron to prioritize native desktop behavior and reduced deployment/runtime complexity for Linux.
- Explicit refresh orchestration is straightforward for MVP state management; alternative global event buses or reactive stores would add complexity early.

## 3) Key domain decisions and their rationale

### 3.1 Strict task status transition map

- The model/service enforce allowed state transitions via `ALLOWED_TRANSITIONS` + `transition_status()` validation.

**Why this path?**
- This prevents illegal task lifecycle jumps and protects reporting correctness.
- Alternative permissive updates (`task.status = ...`) were rejected because they shift validation burden to every UI path.

### 3.2 Recurring tasks are cloned on completion

- Completing a recurring task creates the next task instance and links it back through `parent_task_id`.

**Why this path?**
- It preserves a full execution history and immutable past records.
- Alternative single-row “rolling due date” models are simpler but weaken auditability and historical analytics.

### 3.3 Default room fallback (`General`)

- `create_task()` ensures there is always at least one room context by creating/using a default `General` room if needed.

**Why this path?**
- Reduces friction for fast task capture and avoids `NULL`-heavy task topology.
- Alternative forcing room selection on every create increases data cleanliness but hurts UX and speed in MVP workflows.

### 3.4 Controlled seed data with deterministic IDs

- Alembic revisions seed asset categories and attribute definitions using fixed UUID patterns.

**Why this path (somewhat uncommon)?**
- Deterministic IDs make upgrades/downgrades predictable and allow reference integrity across environments.
- Alternative random UUID seeding is common but makes deterministic diffs and rollback targeting harder.

## 4) Python libraries used and why

## 4.1 Runtime dependencies

- **PySide6**: Native Qt-based desktop UI framework.
  - Chosen for robust desktop widgets, mature Linux support, and no browser shell dependency.
- **SQLAlchemy 2.x**: ORM + SQL expression layer.
  - Chosen for typed models, composable queries, and portability compared with ad-hoc SQL.
- **Alembic**: Schema/data migration management.
  - Chosen so schema + seed evolution is versioned instead of hidden in startup scripts.
- **tomli-w**: TOML writing utility.
  - Chosen for simple config persistence in a human-readable format.

## 4.2 Standard library usage worth noting

- `dataclasses`: DTOs and config path container (`slots=True` for lighter objects).
- `logging` + `RotatingFileHandler`: bounded log files suitable for local desktop apps.
- `hashlib` + `shutil`: backup copy + checksum verification.
- `pathlib`: cross-platform filesystem path handling.

## 4.3 Dev/test dependency

- **pytest** (optional `dev` extra): unit/integration-style tests of service workflows using in-memory SQLite.

**Why these choices vs alternatives?**
- We prioritized low operational overhead and strong local determinism.
- We did not adopt heavier stacks (e.g., FastAPI backend + browser frontend) because the product target is a native local-first Linux desktop MVP.

## 5) Project setup and packaging

- Build backend: `setuptools.build_meta` with `wheel`.
- Python requirement: `>=3.12`.
- Package layout: top-level package `homepal` with explicit subpackages in setuptools config.
- App entry today is script-style (`python main.py`) rather than an installed console script.

**Why this path?**
- For MVP velocity, script launch is the shortest feedback loop.
- Alternative packaging with dedicated `entry_points.console_scripts` can be added later for distribution polish.
- Explicit package listing is simple and predictable in early-stage repos; auto-discovery could be adopted as package surface grows.

## 6) Data and configuration layout

Homepal stores local state in user-scoped directories:

- Database: `~/.local/share/homepal/homepal.db`
- Logs: `~/.local/share/homepal/logs/homepal.log`
- Config: `~/.config/homepal/config.toml`

**Why this path?**
- Follows Linux/XDG-style conventions and avoids requiring admin privileges.
- Alternative single working-directory storage is easier for prototypes but brittle for real user environments.

## 7) Testing approach in this repo

- Tests focus on service-level behavior (status transitions, recurrence generation, topology links, deletion guards, reporting/calendaring).
- In-memory SQLite (`sqlite:///:memory:`) keeps tests fast and deterministic.

**Why this path?**
- Service tests catch most business regressions without brittle GUI automation.
- Alternative end-to-end GUI tests are valuable later, but typically costlier and less stable for early MVP iteration.

## 8) Notable trade-offs and future evolution

Current choices intentionally optimize for MVP reliability and maintainability over maximal abstraction:

- **Single-session desktop process** is simple, but eventually may evolve to session-per-unit-of-work if concurrency or background workers are introduced.
- **Large `TaskService`** is coherent for now, but can be split into bounded context services as domain complexity increases.
- **`Base.metadata.create_all()` at startup** is convenient in scaffold stage; in production-hardening phases this can be replaced by strict migration-only schema management.

That said, the present setup gives a clean and testable foundation: explicit domain model, centralized business rules, deterministic seeding, and native desktop presentation.
