import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0

ItemDelegate {
    id: row
    property bool active: false
    width: parent ? parent.width : implicitWidth
    height: 64
    background: Rectangle {
        radius: Theme.radiusM
        color: row.active ? Theme.selected : (row.hovered ? Theme.hover : "transparent")
        Behavior on color { ColorAnimation { duration: 100 } }
    }
    contentItem: RowLayout {
        Label { text: model.title; color: Theme.textPrimary; font.weight: Font.Medium; Layout.fillWidth: true }
        Label { text: model.priority; color: Theme.textSecondary; font.pixelSize: 12 }
        Label { text: model.due; color: model.isOverdue ? Theme.warning : Theme.textMuted; font.pixelSize: 12 }
    }
}
