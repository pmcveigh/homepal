import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0
import ../components

ColumnLayout {
    property string title: ""
    anchors.centerIn: parent
    spacing: Theme.spacingS
    Label { text: title; color: Theme.textPrimary; font.pixelSize: 30 }
    Label { text: "Screen scaffolded in the new QML system."; color: Theme.textMuted }
}
