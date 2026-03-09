from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    app.setFont(QFont("SF Pro Text", 10))
    app.setStyleSheet(DARK_STYLESHEET)


DARK_STYLESHEET = """
QWidget {
    background-color: #131416;
    color: #e8e9ec;
    font-size: 13px;
}
QMainWindow, #appShell {
    background-color: #101113;
}
#sidebarNav {
    background-color: #17181b;
    border-right: 1px solid #2b2d32;
}
#sidebarBrand {
    color: #f4f5f7;
    font-size: 18px;
    font-weight: 600;
    padding: 6px 0 12px 6px;
}
QListWidget#sidebarList {
    background: transparent;
    border: none;
    outline: 0;
}
QListWidget#sidebarList::item {
    border-radius: 9px;
    padding: 10px 12px;
    margin: 2px 0;
    color: #c4c8d1;
}
QListWidget#sidebarList::item:hover { background: #22242a; }
QListWidget#sidebarList::item:selected {
    background: #2a3955;
    color: #eef4ff;
}
#sectionPage {
    background: #121315;
}
#sectionHeader {
    background: #17191d;
    border: 1px solid #2a2d33;
    border-radius: 12px;
    padding: 8px;
}
#sectionTitle {
    font-size: 23px;
    font-weight: 600;
    color: #f5f6f7;
}
#sectionSubtitle {
    color: #9aa0ac;
    font-size: 12px;
}
QLineEdit#searchBar {
    background: #22252a;
    border: 1px solid #32353c;
    border-radius: 9px;
    padding: 8px 10px;
}
QLineEdit#searchBar:focus, QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QDateTimeEdit:focus {
    border: 1px solid #5b87d7;
}
QPushButton, QToolButton {
    background: #252931;
    border: 1px solid #343944;
    border-radius: 9px;
    padding: 7px 11px;
}
QPushButton:hover, QToolButton:hover { background: #2d323d; }
QPushButton:pressed, QToolButton:pressed { background: #1f232b; }
QPushButton#quickAddButton {
    background: #3d5f96;
    border-color: #4a73b7;
    color: #f7f9ff;
    font-weight: 600;
}
#contentCard {
    background: #1b1d21;
    border: 1px solid #2b2e35;
    border-radius: 12px;
}
#dashboardTileTitle { font-size: 12px; color: #99a1af; }
#dashboardTileValue { font-size: 26px; font-weight: 600; }
#inspectorPanel {
    background: #191b1f;
    border: 1px solid #2a2d35;
    border-radius: 12px;
}
QTableView, QListWidget, QTreeWidget, QTabWidget::pane {
    background: #191b1f;
    border: 1px solid #2a2d33;
    border-radius: 8px;
    gridline-color: #2a2d33;
}
QHeaderView::section {
    background: #1f2228;
    color: #aeb5c2;
    border: none;
    border-right: 1px solid #2c3139;
    padding: 8px;
}
QTableView::item:selected, QListWidget::item:selected {
    background: #2b3d5f;
}
QTabBar::tab {
    background: #1b1d21;
    border: 1px solid #2a2d33;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 7px 10px;
    margin-right: 3px;
    color: #aeb5c2;
}
QTabBar::tab:selected {
    background: #242832;
    color: #f0f2f7;
}
QLabel#mutedLabel { color: #9ba2af; }
QLabel#statusBadge {
    border-radius: 7px;
    background: #283243;
    color: #d5e4ff;
    padding: 2px 8px;
    font-size: 11px;
}
QStatusBar {
    background: #131518;
    border-top: 1px solid #2a2d33;
    color: #97a0af;
}
"""
