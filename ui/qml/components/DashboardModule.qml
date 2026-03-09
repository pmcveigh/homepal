import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0

Rectangle {
    property string title: ""
    default property alias content: body.data
    radius: Theme.radiusL
    color: Theme.surface1
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingM
        spacing: Theme.spacingS
        Label { text: title; color: Theme.textSecondary; font.pixelSize: 14; font.weight: Font.DemiBold }
        ColumnLayout { id: body; Layout.fillWidth: true }
    }
}
