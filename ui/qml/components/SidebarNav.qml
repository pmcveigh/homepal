import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import "."

Rectangle {
    id: root
    property var items: []
    property string current: "Dashboard"
    signal selected(string screen)

    color: Theme.sidebar
    implicitWidth: 240

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingM
        spacing: Theme.spacingS

        Label { text: "Homepal"; color: Theme.textPrimary; font.pixelSize: 20; font.weight: Font.DemiBold }
        Label { text: "Household operations"; color: Theme.textMuted; font.pixelSize: 12 }

        Repeater {
            model: root.items
            delegate: SidebarItem {
                text: modelData
                active: root.current === modelData
                onClicked: root.selected(modelData)
            }
        }
        Item { Layout.fillHeight: true }
    }
}
