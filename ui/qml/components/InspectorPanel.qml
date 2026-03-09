import QtQuick
import QtQuick.Layouts
import ../theme 1.0

Rectangle {
    radius: Theme.radiusL
    color: Theme.surface2
    Layout.minimumWidth: 310
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingM
        spacing: Theme.spacingM
    }
}
