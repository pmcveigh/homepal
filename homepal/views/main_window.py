from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QSplitter, QStackedWidget, QStatusBar

from homepal.services.task_service import TaskService
from homepal.ui.components import QuickAddButton, SearchBar, SectionPage, SidebarNav
from homepal.widgets.budget_finance_panel import BudgetFinancePanel
from homepal.widgets.calendar_panel import CalendarPanel
from homepal.widgets.dashboard_panel import DashboardPanel
from homepal.widgets.household_members_panel import HouseholdMembersPanel
from homepal.widgets.meal_planning_panel import MealPlanningPanel
from homepal.widgets.providers_panel import ProvidersPanel
from homepal.widgets.rooms_assets_panel import AssetsTab, RoomsTab
from homepal.widgets.shopping_panel import ShoppingPanel
from homepal.widgets.task_panel import TaskPanel


class MainWindow(QMainWindow):
    SECTIONS = [
        "Dashboard",
        "Tasks",
        "Rooms",
        "Assets",
        "Providers",
        "Calendar",
        "Budget & Finance",
        "Household Members",
        "Meal Planning & Shopping",
    ]

    def __init__(self, task_service: TaskService):
        super().__init__()
        self.task_service = task_service
        self.setWindowTitle("Homepal")
        self.resize(1440, 860)

        shell = QSplitter()
        shell.setObjectName("appShell")
        self.nav = SidebarNav(self.SECTIONS)
        self.stack = QStackedWidget()

        self.dashboard_panel = DashboardPanel(self.task_service)
        self.task_panel = TaskPanel(self.task_service)
        self.task_panel.data_changed.connect(self.refresh_views)
        self.rooms_panel = RoomsTab(self.task_service, self.refresh_views)
        self.assets_panel = AssetsTab(self.task_service, self.refresh_views)
        self.providers_panel = ProvidersPanel(self.task_service, self.refresh_views)
        self.calendar_panel = CalendarPanel(self.task_service)
        self.budget_finance_panel = BudgetFinancePanel(self.task_service)
        self.household_members_panel = HouseholdMembersPanel(self.task_service, self.refresh_views)
        self.meal_planning_panel = MealPlanningPanel()
        self.shopping_panel = ShoppingPanel(self.task_service)

        self._add_section("Dashboard", "Operational home overview and fast entry points", self.dashboard_panel)
        self._add_task_section()
        self._add_section("Rooms", "Manage household spaces and linked context", self.rooms_panel, add_action=("Add Room", self.rooms_panel._add_room))
        self._add_section("Assets", "Track equipment, warranties and maintenance", self.assets_panel, add_action=("Add Asset", self.assets_panel._add_asset))
        self._add_section("Providers", "Services, contracts and renewal responsibilities", self.providers_panel, add_action=("Add Provider", self.providers_panel._new_provider))
        self._add_section("Calendar", "Schedule linked home events and due dates", self.calendar_panel)
        self._add_section("Budget & Finance", "Sober household budget tracking", self.budget_finance_panel)
        self._add_section("Household Members", "Workload and assignments", self.household_members_panel, add_action=("Add Member", self.household_members_panel.add_member))
        self._add_meal_shopping_section()

        shell.addWidget(self.nav)
        shell.addWidget(self.stack)
        shell.setSizes([250, 1190])
        self.setCentralWidget(shell)

        self.nav.section_changed.connect(self.stack.setCurrentIndex)
        self.nav.set_current(0)

        self.setStatusBar(QStatusBar())
        self.update_status_bar()

    def _add_section(self, title: str, subtitle: str, content, add_action: tuple[str, callable] | None = None) -> None:
        page = SectionPage(title, subtitle)
        if add_action:
            page.header.add_action_widget(QuickAddButton(add_action[0], add_action[1]))
        page.content_layout.addWidget(content)
        self.stack.addWidget(page)

    def _add_task_section(self) -> None:
        page = SectionPage("Tasks", "Operational center with linked rooms, assets, members and providers")
        search = SearchBar("Search tasks")
        search.textChanged.connect(self.task_panel.search_input.setText)
        page.header.add_action_widget(search)
        page.header.add_action_widget(QuickAddButton("Add Task", self.task_panel._new_task))
        page.content_layout.addWidget(self.task_panel)
        self.stack.addWidget(page)

    def _add_meal_shopping_section(self) -> None:
        panel = QSplitter()
        panel.addWidget(self.meal_planning_panel)
        panel.addWidget(self.shopping_panel)
        panel.setSizes([540, 540])
        self._add_section("Meal Planning & Shopping", "Plan meals and execute generated shopping", panel)

    def refresh_views(self) -> None:
        self.dashboard_panel.refresh()
        self.task_panel.refresh_topology()
        self.task_panel.refresh()
        self.rooms_panel.refresh()
        self.assets_panel.refresh()
        self.providers_panel.refresh()
        self.household_members_panel.refresh()
        self.calendar_panel.refresh()
        self.budget_finance_panel.refresh()
        self.shopping_panel.refresh()
        self.update_status_bar()

    def update_status_bar(self) -> None:
        stats = self.task_service.get_dashboard_stats()
        self.statusBar().showMessage(
            f"Open {stats.open_tasks}   Overdue {stats.overdue_tasks}   P1 {stats.p1_tasks}   Due this week {stats.due_this_week}   Rooms {stats.total_rooms}   Assets {stats.total_assets}"
        )
