import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "theme" 1.0
import "components"
import "screens"

ApplicationWindow {
    visible: true
    width: 1500
    height: 900
    title: "Homepal"
    color: Theme.bg

    property var navItems: [
        "Dashboard", "Tasks", "Rooms", "Assets", "Providers", "Calendar", "Budget & Finance", "Household Members", "Meal Planning & Shopping"
    ]

    RowLayout {
        anchors.fill: parent
        spacing: 0

        SidebarNav {
            Layout.fillHeight: true
            items: navItems
            current: appController.currentScreen
            onSelected: appController.navigate(screen)
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Theme.bg

            Loader {
                id: screenLoader
                anchors.fill: parent
                sourceComponent: {
                    switch (appController.currentScreen) {
                    case "Dashboard": return dashboardScreen
                    case "Tasks": return tasksScreen
                    case "Rooms": return roomsScreen
                    case "Assets": return assetsScreen
                    default: return placeholderScreen
                    }
                }
            }
        }
    }

    Component { id: dashboardScreen; DashboardScreen {} }
    Component { id: tasksScreen; TasksScreen {} }
    Component { id: roomsScreen; RoomsScreen {} }
    Component { id: assetsScreen; AssetsScreen {} }
    Component { id: placeholderScreen; PlaceholderScreen { title: appController.currentScreen } }
}
