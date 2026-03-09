import QtQuick
import QtQuick.Controls
import ../theme 1.0

ItemDelegate {
    id: root
    property bool active: false
    width: parent ? parent.width : implicitWidth
    height: 42
    background: Rectangle {
        radius: Theme.radiusM
        color: root.active ? Theme.selected : (root.hovered ? Theme.hover : "transparent")
        Behavior on color { ColorAnimation { duration: 120 } }
    }
    contentItem: Text {
        text: root.text
        color: Theme.textPrimary
        font.pixelSize: 14
        verticalAlignment: Text.AlignVCenter
    }
}
