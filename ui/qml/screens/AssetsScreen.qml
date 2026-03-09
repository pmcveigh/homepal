import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import ../components

ColumnLayout {
    anchors.fill: parent
    anchors.margins: Theme.spacingL
    spacing: Theme.spacingM
    PageHeader { title: "Assets"; subtitle: "Maintenance and lifecycle" }
    Rectangle { color: Theme.surface1; radius: Theme.radiusL; Layout.fillWidth: true; Layout.fillHeight: true
        ListView { anchors.fill: parent; anchors.margins: Theme.spacingS; model: appController.assetsModel
            delegate: ItemDelegate { width: parent.width; text: model.name + " · " + model.category
                background: Rectangle { color: hovered ? Theme.hover : "transparent"; radius: Theme.radiusM } }
        }
    }
}
