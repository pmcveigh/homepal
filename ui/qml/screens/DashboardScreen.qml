import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import ../components

Flickable {
    clip: true
    contentWidth: width
    contentHeight: content.implicitHeight + Theme.spacingL * 2
    ColumnLayout {
        id: content
        width: parent.width - Theme.spacingL * 2
        x: Theme.spacingL
        y: Theme.spacingL
        spacing: Theme.spacingM

        PageHeader { title: "Dashboard"; subtitle: "Operational overview" }
        MetricStrip { metricModel: appController.dashboardMetricsModel; Layout.fillWidth: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingM
            DashboardModule {
                Layout.fillWidth: true
                title: "Upcoming tasks"
                Repeater {
                    model: appController.upcomingTasksModel
                    delegate: Label {
                        text: model.title + " · " + model.dueLabel + " · " + model.room
                        color: Theme.textSecondary
                        font.pixelSize: 13
                    }
                }
            }
            DashboardModule {
                Layout.fillWidth: true
                title: "Room alerts"
                Repeater {
                    model: appController.roomAlertsModel
                    delegate: Label {
                        text: model.title + " · " + model.room
                        color: Theme.warning
                        font.pixelSize: 13
                    }
                }
            }
        }
    }
}
