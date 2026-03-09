from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from homepal.services.task_service import TaskService
from homepal.ui.components import ContentCard, DashboardTile


class DashboardPanel(QWidget):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        stats_card = ContentCard()
        grid = QGridLayout(stats_card)
        grid.setContentsMargins(12, 12, 12, 12)
        grid.setSpacing(10)

        self.open_tile = DashboardTile("Open tasks")
        self.overdue_tile = DashboardTile("Overdue")
        self.today_tile = DashboardTile("Due this week")
        self.p1_tile = DashboardTile("High priority")
        self.rooms_tile = DashboardTile("Rooms")
        self.assets_tile = DashboardTile("Assets")

        tiles = [self.open_tile, self.overdue_tile, self.today_tile, self.p1_tile, self.rooms_tile, self.assets_tile]
        for i, tile in enumerate(tiles):
            grid.addWidget(tile, i // 3, i % 3)
        layout.addWidget(stats_card)

        lower = QGridLayout()
        lower.setSpacing(12)
        self.upcoming_list = self._build_list_card("Upcoming tasks")
        self.room_alerts_list = self._build_list_card("Room alerts")
        self.maintenance_list = self._build_list_card("Asset maintenance")
        lower.addWidget(self.upcoming_list.parentWidget(), 0, 0)
        lower.addWidget(self.room_alerts_list.parentWidget(), 0, 1)
        lower.addWidget(self.maintenance_list.parentWidget(), 1, 0, 1, 2)
        layout.addLayout(lower)

        self.refresh()

    def _build_list_card(self, title: str) -> QListWidget:
        card = ContentCard()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        heading = QLabel(title)
        heading.setObjectName("sectionSubtitle")
        lst = QListWidget()
        lst.setAlternatingRowColors(False)
        lay.addWidget(heading)
        lay.addWidget(lst)
        return lst

    def refresh(self) -> None:
        stats = self.task_service.get_dashboard_stats()
        self.open_tile.value_label.setText(str(stats.open_tasks))
        self.overdue_tile.value_label.setText(str(stats.overdue_tasks))
        self.p1_tile.value_label.setText(str(stats.p1_tasks))
        self.today_tile.value_label.setText(str(stats.due_this_week))
        self.rooms_tile.value_label.setText(str(stats.total_rooms))
        self.assets_tile.value_label.setText(str(stats.total_assets))

        filters = self.task_service.build_task_filters()
        rows = self.task_service.list_tasks_for_table(filters)[:20]
        self.upcoming_list.clear()
        self.room_alerts_list.clear()
        self.maintenance_list.clear()
        for row in rows:
            due = row.due_date.strftime("%d %b") if row.due_date else "No due"
            line = f"{row.title} · {due}"
            item = QListWidgetItem(line)
            item.setData(Qt.UserRole, row.id)
            self.upcoming_list.addItem(item)
            if row.is_overdue:
                self.room_alerts_list.addItem(f"{row.room_name or 'General'} · {row.title}")
            if row.is_recurring:
                self.maintenance_list.addItem(f"{row.asset_names[0] if row.asset_names else 'House'} · {row.title}")
        if self.room_alerts_list.count() == 0:
            self.room_alerts_list.addItem("No active alerts")
        if self.maintenance_list.count() == 0:
            self.maintenance_list.addItem("No maintenance due")
