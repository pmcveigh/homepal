from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SidebarNav(QWidget):
    section_changed = Signal(int)

    def __init__(self, sections: list[str]):
        super().__init__()
        self.setObjectName("sidebarNav")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        brand = QLabel("Homepal")
        brand.setObjectName("sidebarBrand")
        layout.addWidget(brand)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("sidebarList")
        for section in sections:
            QListWidgetItem(section, self.list_widget)
        self.list_widget.currentRowChanged.connect(self.section_changed)
        layout.addWidget(self.list_widget, 1)

    def set_current(self, index: int) -> None:
        self.list_widget.setCurrentRow(index)


class SearchBar(QLineEdit):
    def __init__(self, placeholder: str = "Search"):
        super().__init__()
        self.setObjectName("searchBar")
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)


class QuickAddButton(QPushButton):
    def __init__(self, label: str, callback: Callable[[], None] | None = None):
        super().__init__(label)
        self.setObjectName("quickAddButton")
        if callback:
            self.clicked.connect(callback)


class SectionHeader(QFrame):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("sectionHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        titles = QVBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("sectionSubtitle")
        self.subtitle_label.setVisible(bool(subtitle))
        titles.addWidget(self.title_label)
        titles.addWidget(self.subtitle_label)
        layout.addLayout(titles)
        layout.addStretch(1)
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(8)
        layout.addLayout(self.action_layout)

    def add_action_widget(self, widget: QWidget) -> None:
        self.action_layout.addWidget(widget)


class ContentCard(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("contentCard")


class DashboardTile(ContentCard):
    def __init__(self, title: str, value: str = "0", detail: str = ""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        t = QLabel(title)
        t.setObjectName("dashboardTileTitle")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("dashboardTileValue")
        self.detail_label = QLabel(detail)
        self.detail_label.setObjectName("mutedLabel")
        self.detail_label.setWordWrap(True)
        self.detail_label.setVisible(bool(detail))
        layout.addWidget(t)
        layout.addWidget(self.value_label)
        layout.addWidget(self.detail_label)
        layout.addStretch(1)


class InspectorPanel(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("inspectorPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        heading = QLabel(title)
        heading.setObjectName("sectionSubtitle")
        layout.addWidget(heading)
        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        layout.addLayout(self.body)
        layout.addStretch(1)


class SectionPage(QWidget):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        self.setObjectName("sectionPage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.header = SectionHeader(title, subtitle)
        layout.addWidget(self.header)
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.content_layout, 1)
