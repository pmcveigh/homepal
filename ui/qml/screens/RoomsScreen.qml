import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import ../components

ColumnLayout {
    anchors.fill: parent
    anchors.margins: Theme.spacingL
    spacing: Theme.spacingM
    PageHeader { title: "Rooms"; subtitle: "Room context and workload" }
    Rectangle {
        color: Theme.surface1
        radius: Theme.radiusL
        Layout.fillWidth: true
        Layout.fillHeight: true
        ListView {
            anchors.fill: parent
            anchors.margins: Theme.spacingS
            model: appController.roomsModel
            delegate: ItemDelegate {
                width: parent.width
                text: model.name + " · Assets " + model.assets + " · Open " + model.openTasks
                background: Rectangle { color: hovered ? Theme.hover : "transparent"; radius: Theme.radiusM }
            }
        }
    }
}
