from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from homepal.db import Base


class Priority(str, enum.Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TaskStatus(str, enum.Enum):
    DRAFT = "Draft"
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"
    ARCHIVED = "Archived"


class LinkRole(str, enum.Enum):
    ABOUT = "about"
    USES = "uses"
    REQUIRES = "requires"


class AttachmentOwner(str, enum.Enum):
    TASK = "task"
    ASSET = "asset"


class ValueType(str, enum.Enum):
    TEXT = "text"
    INT = "int"
    DECIMAL = "decimal"
    BOOL = "bool"
    DATE = "date"
    CHOICE = "choice"


class RecurrenceType(str, enum.Enum):
    EVERY_N_DAYS = "every_n_days"
    EVERY_N_MONTHS = "every_n_months"
    FIXED_ANNUAL_DATE = "fixed_annual_date"
    AFTER_COMPLETION_N_DAYS = "after_completion_n_days"


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (Index("ux_rooms_name", "name", unique=True),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    floor_level: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("asset_categories.id"))
    installation_date: Mapped[date | None] = mapped_column(Date)
    warranty_expiry: Mapped[date | None] = mapped_column(Date)
    last_serviced_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)


class AssetRoomLink(Base):
    __tablename__ = "asset_room_links"
    __table_args__ = (
        Index("ix_asset_room_room_id", "room_id"),
        Index("ix_asset_room_asset_id", "asset_id"),
    )

    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), primary_key=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    location_notes: Mapped[str | None] = mapped_column(String(200))


class RecurringSchedule(Base):
    __tablename__ = "recurring_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recurrence_type: Mapped[RecurrenceType] = mapped_column(Enum(RecurrenceType), nullable=False)
    interval_value: Mapped[int | None]
    anchor_date: Mapped[date | None] = mapped_column(Date)
    completion_offset: Mapped[int | None]


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("room_id IS NOT NULL OR asset_id IS NOT NULL", name="ck_task_room_or_asset"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_due_date", "due_date"),
        Index("ix_tasks_room_id", "room_id"),
        Index("ix_tasks_asset_id", "asset_id"),
        Index("ix_tasks_parent_task_id", "parent_task_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.DRAFT, nullable=False)
    room_id: Mapped[str | None] = mapped_column(ForeignKey("rooms.id"))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"))
    recurring_schedule_id: Mapped[str | None] = mapped_column(ForeignKey("recurring_schedules.id"))
    parent_task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    due_date: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now)
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    actual_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    requires_follow_up: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_effort_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    labels: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    recurring_schedule: Mapped[RecurringSchedule | None] = relationship()


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_type: Mapped[AttachmentOwner] = mapped_column(Enum(AttachmentOwner), default=AttachmentOwner.TASK, nullable=False)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"))
    file_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    field_changed: Mapped[str] = mapped_column(String(120), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    user_identifier: Mapped[str] = mapped_column(String(255), nullable=False)


class TaskRoomLink(Base):
    __tablename__ = "task_room_links"

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), primary_key=True)


class TaskAssetLink(Base):
    __tablename__ = "task_asset_links"
    __table_args__ = (
        Index("ix_task_asset_asset_id", "asset_id"),
        Index("ix_task_asset_role", "role"),
    )

    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), primary_key=True)
    role: Mapped[LinkRole] = mapped_column(Enum(LinkRole), primary_key=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    unit: Mapped[str | None] = mapped_column(String(30))


class AttributeDefinition(Base):
    __tablename__ = "attribute_definitions"
    __table_args__ = (
        Index("ix_attr_def_scope", "applies_to", "category_id", "room_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    applies_to: Mapped[str] = mapped_column(String(10), nullable=False)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("asset_categories.id"))
    room_type: Mapped[str | None] = mapped_column(String(40))
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    value_type: Mapped[ValueType] = mapped_column(Enum(ValueType), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    choices_csv: Mapped[str | None] = mapped_column(Text)
    required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    searchable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    filterable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AttributeValue(Base):
    __tablename__ = "attribute_values"
    __table_args__ = (
        Index("ix_attr_values_room_id", "room_id"),
        Index("ix_attr_values_asset_id", "asset_id"),
        Index("ix_attr_values_definition_id", "definition_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id: Mapped[str | None] = mapped_column(ForeignKey("rooms.id"))
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"))
    definition_id: Mapped[str] = mapped_column(ForeignKey("attribute_definitions.id"), nullable=False)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_int: Mapped[int | None]
    value_decimal: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    value_date: Mapped[date | None] = mapped_column(Date)


ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.DRAFT: {TaskStatus.OPEN},
    TaskStatus.OPEN: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
    TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED},
    TaskStatus.BLOCKED: {TaskStatus.OPEN},
    TaskStatus.COMPLETED: {TaskStatus.ARCHIVED},
    TaskStatus.ARCHIVED: set(),
}



def compute_next_due_date(schedule: RecurringSchedule, completed_on: date) -> date:
    if schedule.recurrence_type == RecurrenceType.EVERY_N_DAYS:
        return completed_on + timedelta(days=schedule.interval_value or 0)
    if schedule.recurrence_type == RecurrenceType.AFTER_COMPLETION_N_DAYS:
        return completed_on + timedelta(days=schedule.completion_offset or 0)
    if schedule.recurrence_type == RecurrenceType.EVERY_N_MONTHS:
        months = schedule.interval_value or 1
        start = schedule.anchor_date or completed_on
        year = start.year + ((start.month - 1 + months) // 12)
        month = (start.month - 1 + months) % 12 + 1
        day = min(start.day, 28)
        return date(year, month, day)
    if schedule.recurrence_type == RecurrenceType.FIXED_ANNUAL_DATE:
        start = schedule.anchor_date or completed_on
        month = start.month
        day = start.day
        candidate = date(completed_on.year, month, min(day, 28))
        return candidate if candidate > completed_on else date(completed_on.year + 1, month, min(day, 28))
    raise ValueError(f"Unknown recurrence type: {schedule.recurrence_type}")
