import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import ../theme 1.0

ColumnLayout {
    property string title: "No records"
    property string subtitle: "Try adjusting filters"
    anchors.centerIn: parent
    Label { text: title; color: Theme.textSecondary; font.pixelSize: 15 }
    Label { text: subtitle; color: Theme.textMuted; font.pixelSize: 12 }
}
