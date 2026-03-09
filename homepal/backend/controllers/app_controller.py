from __future__ import annotations

from datetime import date

from PySide6.QtCore import Property, QObject, Signal, Slot

from homepal.models import TaskStatus
from homepal.services.task_service import TaskListFilters, TaskService

from homepal.backend.viewmodels.list_models import DictListModel


class AppController(QObject):
    currentScreenChanged = Signal()
    selectedTaskChanged = Signal()
    tasksChanged = Signal()

    def __init__(self, task_service: TaskService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._service = task_service
        self._current_screen = "Dashboard"
        self._task_search = ""
        self._task_status_filter = "all"
        self._task_due_filter = "any"
        self._selected_task: dict = {}

        self._dashboard_metrics_model = DictListModel(self)
        self._upcoming_tasks_model = DictListModel(self)
        self._room_alerts_model = DictListModel(self)

        self._task_list_model = DictListModel(self)
        self._rooms_model = DictListModel(self)
        self._assets_model = DictListModel(self)
        self._providers_model = DictListModel(self)

        self.refresh_all()

    @Property(str, notify=currentScreenChanged)
    def currentScreen(self) -> str:  # noqa: N802
        return self._current_screen

    @currentScreen.setter
    def currentScreen(self, value: str) -> None:  # noqa: N802
        if value == self._current_screen:
            return
        self._current_screen = value
        self.currentScreenChanged.emit()

    @Property("QVariantMap", notify=selectedTaskChanged)
    def selectedTask(self):  # noqa: N802
        return self._selected_task

    @Property(QObject, constant=True)
    def dashboardMetricsModel(self) -> QObject:  # noqa: N802
        return self._dashboard_metrics_model

    @Property(QObject, constant=True)
    def upcomingTasksModel(self) -> QObject:  # noqa: N802
        return self._upcoming_tasks_model

    @Property(QObject, constant=True)
    def roomAlertsModel(self) -> QObject:  # noqa: N802
        return self._room_alerts_model

    @Property(QObject, constant=True)
    def taskListModel(self) -> QObject:  # noqa: N802
        return self._task_list_model

    @Property(QObject, constant=True)
    def roomsModel(self) -> QObject:  # noqa: N802
        return self._rooms_model

    @Property(QObject, constant=True)
    def assetsModel(self) -> QObject:  # noqa: N802
        return self._assets_model

    @Property(QObject, constant=True)
    def providersModel(self) -> QObject:  # noqa: N802
        return self._providers_model

    @Slot(str)
    def navigate(self, screen_name: str) -> None:
        self.currentScreen = screen_name

    @Slot()
    def refresh_all(self) -> None:
        self._refresh_dashboard()
        self._refresh_tasks()
        self._refresh_rooms()
        self._refresh_assets()
        self._refresh_providers()

    def _refresh_dashboard(self) -> None:
        stats = self._service.get_dashboard_stats()
        self._dashboard_metrics_model.set_rows(
            [
                {"label": "Open tasks", "value": stats.open_tasks},
                {"label": "Overdue", "value": stats.overdue_tasks},
                {"label": "Due this week", "value": stats.due_this_week},
                {"label": "Rooms", "value": stats.total_rooms},
                {"label": "Assets", "value": stats.total_assets},
                {"label": "P1", "value": stats.p1_tasks},
            ]
        )

        upcoming = []
        alerts = []
        for row in self._service.list_task_rows(TaskListFilters(due_range="week"))[:8]:
            due_label = row.due_date.strftime("%b %d") if row.due_date else "No due date"
            entry = {
                "id": row.id,
                "title": row.title,
                "dueLabel": due_label,
                "room": row.room_name or "General",
                "priority": row.priority.value,
                "status": row.status.value,
                "isOverdue": row.is_overdue,
            }
            upcoming.append(entry)
            if row.is_overdue:
                alerts.append(entry)

        self._upcoming_tasks_model.set_rows(upcoming)
        self._room_alerts_model.set_rows(alerts[:6])

    def _task_filters(self) -> TaskListFilters:
        statuses = []
        if self._task_status_filter != "all":
            statuses = [TaskStatus(self._task_status_filter)]
        return TaskListFilters(search=self._task_search, due_range=self._task_due_filter, statuses=statuses)

    def _refresh_tasks(self) -> None:
        rows = self._service.list_task_rows(self._task_filters())
        items = []
        for row in rows:
            items.append(
                {
                    "id": row.id,
                    "title": row.title,
                    "priority": row.priority.value,
                    "status": row.status.value,
                    "room": row.room_name or "General",
                    "assignees": ", ".join(row.assignee_names) if row.assignee_names else "Unassigned",
                    "providers": ", ".join(row.provider_names) if row.provider_names else "—",
                    "due": row.due_date.strftime("%b %d") if row.due_date else "No due",
                    "isOverdue": row.is_overdue,
                    "isDueSoon": row.is_due_this_week,
                    "description": row.description,
                }
            )
        self._task_list_model.set_rows(items)

        if not items:
            self._selected_task = {}
        elif not self._selected_task:
            self._selected_task = items[0]
        else:
            active = next((item for item in items if item["id"] == self._selected_task.get("id")), items[0])
            self._selected_task = active
        self.selectedTaskChanged.emit()
        self.tasksChanged.emit()

    def _refresh_rooms(self) -> None:
        rooms = self._service.list_rooms_overview()
        self._rooms_model.set_rows(
            [
                {
                    "name": room.name,
                    "type": room.room_type,
                    "assets": room.asset_count,
                    "openTasks": room.open_tasks_count,
                    "overdue": room.overdue_tasks_count,
                }
                for room in rooms
            ]
        )

    def _refresh_assets(self) -> None:
        assets = self._service.list_assets()
        self._assets_model.set_rows(
            [{"name": asset.name, "category": asset.category, "notes": asset.notes or ""} for asset in assets]
        )

    def _refresh_providers(self) -> None:
        providers = self._service.list_providers()
        self._providers_model.set_rows(
            [{"name": row.name, "type": row.service_type, "phone": row.phone_number or "—"} for row in providers]
        )

    @Slot(str)
    def setTaskSearch(self, value: str) -> None:  # noqa: N802
        self._task_search = value
        self._refresh_tasks()

    @Slot(str)
    def setTaskStatusFilter(self, value: str) -> None:  # noqa: N802
        self._task_status_filter = value
        self._refresh_tasks()

    @Slot(str)
    def setTaskDueFilter(self, value: str) -> None:  # noqa: N802
        self._task_due_filter = value
        self._refresh_tasks()

    @Slot(int)
    def selectTaskByIndex(self, row: int) -> None:  # noqa: N802
        self._selected_task = self._task_list_model.get(row)
        self.selectedTaskChanged.emit()

    @Slot()
    def markSelectedTaskDone(self) -> None:  # noqa: N802
        task_id = self._selected_task.get("id")
        if not task_id:
            return
        task = next((task for task in self._service.list_tasks() if task.id == task_id), None)
        if not task:
            return
        if task.status in {TaskStatus.OPEN, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED}:
            self._service.transition_status(task, TaskStatus.COMPLETED)
            self._service.session.commit()
            self.refresh_all()
