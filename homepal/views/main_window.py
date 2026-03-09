from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QStatusBar, QTreeWidget, QTreeWidgetItem

from homepal.services.task_service import TaskService
from homepal.widgets.calendar_panel import CalendarPanel
from homepal.widgets.dashboard_panel import DashboardPanel
from homepal.widgets.budget_finance_panel import BudgetFinancePanel
from homepal.widgets.household_members_panel import HouseholdMembersPanel
from homepal.widgets.meal_planning_panel import MealPlanningPanel
from homepal.widgets.providers_panel import ProvidersPanel
from homepal.widgets.reports_panel import ReportsPanel
from homepal.widgets.rooms_assets_panel import RoomsAssetsPanel
from homepal.widgets.shopping_panel import ShoppingPanel
from homepal.widgets.task_panel import TaskPanel


class MainWindow(QMainWindow):
    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service
        self.setWindowTitle("Homepal")
        self.resize(1200, 780)
        splitter = QSplitter(Qt.Horizontal)

        self.nav = QTreeWidget()
        self.nav.setHeaderHidden(True)
        for section in [
            "Dashboard",
            "Tasks",
            "Rooms & Assets",
            "Providers",
            "Calendar",
            "Budget & Finance",
            "Household Members",
            "Meal Planning",
            "Shopping",
            "Reports",
            "Settings",
        ]:
            QTreeWidgetItem(self.nav, [section])

        self.stack = QStackedWidget()
        self.dashboard_panel = DashboardPanel(self.task_service)
        self.stack.addWidget(self.dashboard_panel)

        self.task_panel = TaskPanel(self.task_service)
        self.task_panel.data_changed.connect(self.refresh_views)
        self.stack.addWidget(self.task_panel)

        self.rooms_assets_panel = RoomsAssetsPanel(self.task_service, self.refresh_views)
        self.stack.addWidget(self.rooms_assets_panel)

        self.providers_panel = ProvidersPanel(self.task_service, self.refresh_views)
        self.stack.addWidget(self.providers_panel)

        self.calendar_panel = CalendarPanel(self.task_service)
        self.stack.addWidget(self.calendar_panel)

        self.budget_finance_panel = BudgetFinancePanel(self.task_service)
        self.stack.addWidget(self.budget_finance_panel)

        self.household_members_panel = HouseholdMembersPanel(self.task_service, self.refresh_views)
        self.stack.addWidget(self.household_members_panel)

        self.meal_planning_panel = MealPlanningPanel()
        self.stack.addWidget(self.meal_planning_panel)

        self.shopping_panel = ShoppingPanel(self.task_service)
        self.stack.addWidget(self.shopping_panel)

        self.reports_panel = ReportsPanel(self.task_service)
        self.stack.addWidget(self.reports_panel)

        self.stack.addWidget(self._settings_placeholder())

        self.nav.currentItemChanged.connect(self._on_nav)
        self.nav.setCurrentItem(self.nav.topLevelItem(0))

        splitter.addWidget(self.nav)
        splitter.addWidget(self.stack)
        splitter.setSizes([240, 960])
        self.setCentralWidget(splitter)

        self.setStatusBar(QStatusBar())
        self.update_status_bar()

    def _settings_placeholder(self):
        from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Settings view (MVP scaffold)"))
        return page

    def _on_nav(self, current, _previous):
        if current is None:
            return
        self.stack.setCurrentIndex(self.nav.indexOfTopLevelItem(current))

    def refresh_views(self) -> None:
        self.dashboard_panel.refresh()
        self.task_panel.refresh_topology()
        self.task_panel.refresh()
        self.rooms_assets_panel.refresh()
        self.providers_panel.refresh()
        self.household_members_panel.refresh()
        self.calendar_panel.refresh()
        self.budget_finance_panel.refresh()
        self.shopping_panel.refresh()
        self.update_status_bar()

    def update_status_bar(self) -> None:
        stats = self.task_service.get_dashboard_stats()
        self.statusBar().showMessage(
            f"Open: {stats.open_tasks} | Overdue: {stats.overdue_tasks} | P1: {stats.p1_tasks} | Due this week: {stats.due_this_week} | Rooms: {stats.total_rooms} | Assets: {stats.total_assets}"
        )
