import QtQuick
import QtQuick.Controls
import ../theme 1.0

Button {
    id: root
    property bool active: false
    flat: true
    background: Rectangle {
        radius: Theme.radiusM
        color: root.active ? Theme.selected : (root.hovered ? Theme.hover : Theme.surface2)
    }
    contentItem: Text { text: root.text; color: Theme.textSecondary; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter }
}
