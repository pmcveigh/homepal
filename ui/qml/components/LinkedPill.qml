import QtQuick
import QtQuick.Controls
import ../theme 1.0

Rectangle {
    property string text: ""
    radius: Theme.radiusM
    color: Theme.surface2
    implicitHeight: 26
    implicitWidth: label.implicitWidth + 16
    Label { id: label; anchors.centerIn: parent; text: parent.text; color: Theme.textSecondary; font.pixelSize: 11 }
}
