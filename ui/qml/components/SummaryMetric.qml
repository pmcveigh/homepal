import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import ../theme 1.0

Rectangle {
    property string label: ""
    property string value: ""
    color: "transparent"
    radius: Theme.radiusM
    implicitHeight: 72
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingS
        Label { text: value; color: Theme.textPrimary; font.pixelSize: 24; font.weight: Font.DemiBold }
        Label { text: label; color: Theme.textMuted; font.pixelSize: 12 }
    }
}
